package com.utc.alert.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.utc.alert.common.enums.AlertLevel;
import com.utc.alert.entity.AlertEvent;
import com.utc.alert.entity.AlertGroup;
import com.utc.alert.mapper.AlertGroupMapper;
import com.utc.alert.service.AlertDedupService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.Optional;
import java.util.Set;

@Slf4j
@Service
@RequiredArgsConstructor
public class AlertDedupServiceImpl implements AlertDedupService {

    private static final String KEY_PREFIX = "alert:window:";

    private final StringRedisTemplate redisTemplate;
    private final AlertGroupMapper alertGroupMapper;

    @Value("${alert.dedup.window-minutes:10}")
    private int windowMinutes;

    @Override
    public Optional<Long> tryMerge(AlertEvent alertEvent) {
        if (alertEvent == null || alertEvent.getAreaId() == null) {
            log.warn("AlertDedup: alertEvent or areaId is null, skipping dedup");
            return Optional.empty();
        }

        String areaId = alertEvent.getAreaId();
        String key = KEY_PREFIX + areaId;

        log.info("AlertDedup start: areaId={}, alertEventCode={}, alertLevel={}",
                areaId, alertEvent.getAlertEventCode(), alertEvent.getAlertLevel());

        try {
            long now = alertEvent.getEventTimestamp() != null
                    ? alertEvent.getEventTimestamp()
                    : System.currentTimeMillis();
            long windowStart = now - (long) windowMinutes * 60 * 1000;

            redisTemplate.opsForZSet().removeRangeByScore(key, 0, windowStart);

            Long countInWindow = redisTemplate.opsForZSet().zCard(key);

            if (countInWindow != null && countInWindow > 0) {
                return mergeIntoGroup(alertEvent, areaId, key, now);
            } else {
                createNewGroup(alertEvent, areaId, key, now);
                return Optional.empty();
            }
        } catch (Exception e) {
            log.error("AlertDedup Redis error: areaId={}", areaId, e);
            return Optional.empty();
        }
    }

    private Optional<Long> mergeIntoGroup(AlertEvent alertEvent, String areaId,
                                          String key, long now) {
        AlertGroup group = alertGroupMapper.selectOne(
                new LambdaQueryWrapper<AlertGroup>()
                        .eq(AlertGroup::getAreaId, areaId)
                        .orderByDesc(AlertGroup::getCreatedAt)
                        .last("LIMIT 1"));

        if (group == null) {
            createNewGroup(alertEvent, areaId, key, now);
            return Optional.empty();
        }

        int currentLevelCode = safeLevelCode(group.getHighestLevel());
        int newLevelCode = safeLevelCode(alertEvent.getAlertLevel());
        if (newLevelCode > currentLevelCode) {
            group.setHighestLevel(alertEvent.getAlertLevel());
        }

        group.setTotalCount(group.getTotalCount() + 1);
        group.setWindowEnd(LocalDateTime.ofInstant(
                java.time.Instant.ofEpochMilli(now),
                java.time.ZoneId.systemDefault()));

        alertGroupMapper.updateById(group);

        redisTemplate.opsForZSet().add(key, alertEvent.getAlertEventCode(), now);

        log.info("AlertDedup merged: areaId={}, groupId={}, totalCount={}",
                areaId, group.getId(), group.getTotalCount());

        return Optional.of(group.getId());
    }

    private void createNewGroup(AlertEvent alertEvent, String areaId,
                                String key, long now) {
        LocalDateTime dateTime = LocalDateTime.ofInstant(
                java.time.Instant.ofEpochMilli(now),
                java.time.ZoneId.systemDefault());

        AlertGroup group = new AlertGroup();
        group.setGroupCode("GRP-" + java.util.UUID.randomUUID());
        group.setAreaId(areaId);
        group.setZone(alertEvent.getZone());
        group.setHighestLevel(alertEvent.getAlertLevel());
        group.setTotalCount(1);
        group.setGroupStatus("ACTIVE");
        group.setWindowStart(dateTime);
        group.setWindowEnd(dateTime);

        alertGroupMapper.insert(group);
        redisTemplate.opsForZSet().add(key, alertEvent.getAlertEventCode(), now);

        log.info("AlertDedup created group: areaId={}, groupCode={}, groupId={}",
                areaId, group.getGroupCode(), group.getId());
    }

    private int safeLevelCode(String level) {
        try {
            return AlertLevel.valueOf(level).getCode();
        } catch (Exception e) {
            return 0;
        }
    }
}
