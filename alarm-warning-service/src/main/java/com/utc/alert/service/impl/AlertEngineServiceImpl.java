package com.utc.alert.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.utc.alert.common.enums.AlertLevel;
import com.utc.alert.common.enums.AlertStatus;
import com.utc.alert.dto.MatchResult;
import com.utc.alert.dto.RootCauseResult;
import com.utc.alert.dto.kafka.KafkaMessage;
import com.utc.alert.dto.kafka.LocationInfo;
import com.utc.alert.entity.AlertEvent;
import com.utc.alert.entity.AlertGroup;
import com.utc.alert.mapper.AlertEventMapper;
import com.utc.alert.mapper.AlertGroupMapper;
import com.utc.alert.kafka.producer.AlertEventProducer;
import com.utc.alert.service.AlertDedupService;
import com.utc.alert.service.AlertEngineService;
import com.utc.alert.service.PriorityCalcService;
import com.utc.alert.service.RootCauseService;
import com.utc.alert.service.RuleMatchService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.Comparator;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class AlertEngineServiceImpl implements AlertEngineService {

    private final RuleMatchService ruleMatchService;
    private final RootCauseService rootCauseService;
    private final AlertDedupService alertDedupService;
    private final PriorityCalcService priorityCalcService;
    private final AlertEventProducer alertEventProducer;
    private final AlertEventMapper alertEventMapper;
    private final AlertGroupMapper alertGroupMapper;

    @Override
    public void processMessage(KafkaMessage message) {
        if (message == null) {
            log.warn("Received null Kafka message, skipping");
            return;
        }

        log.info("AlertEngine processing: eventId={}, source={}, eventType={}",
                message.getEventId(), message.getSource(), message.getEventType());

        if (!validateMessage(message)) {
            return;
        }

        List<MatchResult> matchResults;
        try {
            matchResults = ruleMatchService.matchRules(message);
        } catch (Exception e) {
            log.error("Rule matching failed, eventId={}", message.getEventId(), e);
            return;
        }

        if (matchResults == null || matchResults.isEmpty()) {
            log.info("No rules matched, eventId={}, deviceId={}", message.getEventId(), message.getDeviceId());
            return;
        }

        MatchResult highest = matchResults.stream()
                .max(Comparator.comparingInt(r -> AlertLevel.valueOf(r.getAlertLevel()).getCode()))
                .orElse(null);

        if (highest == null) {
            return;
        }

        log.info("Rule matched: eventId={}, ruleCode={}, alertLevel={}",
                message.getEventId(), highest.getRuleCode(), highest.getAlertLevel());

        RootCauseResult rootCauseResult;
        try {
            rootCauseResult = rootCauseService.analyze(message);
        } catch (Exception e) {
            log.error("Root cause analysis failed, eventId={}", message.getEventId(), e);
            rootCauseResult = null;
        }

        try {
            AlertEvent event = buildAlertEvent(message, highest, rootCauseResult);

            try {
                Optional<Long> groupIdOpt = alertDedupService.tryMerge(event);
                if (groupIdOpt.isPresent()) {
                    Long groupId = groupIdOpt.get();
                    event.setAlertGroupId(groupId);
                    AlertGroup group = alertGroupMapper.selectById(groupId);
                    event.setMergedCount(group != null ? group.getTotalCount() : 1);
                } else {
                    AlertGroup newGroup = alertGroupMapper.selectOne(
                            new LambdaQueryWrapper<AlertGroup>()
                                    .eq(AlertGroup::getAreaId, event.getAreaId())
                                    .orderByDesc(AlertGroup::getCreatedAt)
                                    .last("LIMIT 1"));
                    if (newGroup != null) {
                        event.setAlertGroupId(newGroup.getId());
                    }
                    event.setMergedCount(1);
                }
            } catch (Exception e) {
                log.error("Dedup processing failed, eventId={}, skipping dedup",
                        message.getEventId(), e);
                event.setMergedCount(1);
            }

            try {
                int priorityScore = priorityCalcService.calculate(event);
                event.setPriorityScore(priorityScore);
            } catch (Exception e) {
                log.error("Priority calculation failed, eventId={}", message.getEventId(), e);
                event.setPriorityScore(0);
            }

            alertEventMapper.insert(event);
            log.info("Alert event created: alertEventCode={}, alertLevel={}, deviceId={}, alertGroupId={}",
                    event.getAlertEventCode(), event.getAlertLevel(),
                    event.getDeviceId(), event.getAlertGroupId());

            alertEventProducer.send(event);
        } catch (Exception e) {
            log.error("Failed to save alert event, eventId={}", message.getEventId(), e);
        }
    }

    private boolean validateMessage(KafkaMessage message) {
        if (message.getEventId() == null) {
            log.warn("Message missing eventId, skipping");
            return false;
        }
        if (message.getSource() == null) {
            log.warn("Message missing source, eventId={}, skipping", message.getEventId());
            return false;
        }
        if (message.getDeviceId() == null) {
            log.warn("Message missing deviceId, eventId={}, skipping", message.getEventId());
            return false;
        }
        if (message.getTimestamp() == null) {
            log.warn("Message missing timestamp, eventId={}, skipping", message.getEventId());
            return false;
        }
        if (message.getEventType() == null) {
            log.warn("Message missing eventType, eventId={}, skipping", message.getEventId());
            return false;
        }
        return true;
    }

    private AlertEvent buildAlertEvent(KafkaMessage message, MatchResult result,
                                       RootCauseResult rootCauseResult) {
        LocationInfo location = message.getLocation();

        AlertEvent event = new AlertEvent();
        event.setAlertEventCode("ALT-" + UUID.randomUUID());
        event.setSourceEventId(message.getEventId());
        event.setSource(message.getSource());
        event.setDeviceId(message.getDeviceId());
        event.setDeviceType(message.getDeviceType());
        event.setZone(location != null ? location.getZone() : null);
        event.setAreaId(location != null ? location.getAreaId() : null);
        event.setAlertLevel(result.getAlertLevel());
        event.setAlertStatus(AlertStatus.OPEN.name());
        event.setMetricKey(result.getMetricKey());
        event.setMetricValue(result.getMetricValue());
        event.setThresholdValue(result.getThresholdValue());
        if (rootCauseResult != null) {
            event.setRootCause(rootCauseResult.getRootCauseType());
            event.setRootCauseDesc(rootCauseResult.getRootCauseDesc());
        }
        event.setPriorityScore(0);
        event.setMergedCount(1);
        event.setEventTimestamp(message.getTimestamp());
        return event;
    }
}
