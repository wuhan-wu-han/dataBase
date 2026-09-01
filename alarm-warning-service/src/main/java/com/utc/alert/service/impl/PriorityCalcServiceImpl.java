package com.utc.alert.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.utc.alert.common.enums.AlertLevel;
import com.utc.alert.entity.AlertEvent;
import com.utc.alert.entity.AreaPriority;
import com.utc.alert.mapper.AreaPriorityMapper;
import com.utc.alert.service.PriorityCalcService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalTime;
import java.time.ZoneId;

@Slf4j
@Service
@RequiredArgsConstructor
public class PriorityCalcServiceImpl implements PriorityCalcService {

    private static final int DEFAULT_IMPORTANCE = 5;
    private static final BigDecimal DEFAULT_POPULATION_WEIGHT = new BigDecimal("1.0");

    private final AreaPriorityMapper areaPriorityMapper;

    @Override
    public int calculate(AlertEvent alertEvent) {
        if (alertEvent == null) {
            return 1;
        }

        log.info("PriorityCalc start: alertEventCode={}, alertLevel={}",
                alertEvent.getAlertEventCode(), alertEvent.getAlertLevel());

        try {
            int levelWeight = getLevelWeight(alertEvent.getAlertLevel());

            AreaPriority areaPriority = getAreaPriority(alertEvent.getAreaId());
            int importance = areaPriority.getImportance();
            BigDecimal populationWeight = areaPriority.getPopulationWeight();

            int timeWeight = getTimeWeight(alertEvent.getEventTimestamp());

            double raw = levelWeight * 20.0
                    + importance * 15.0
                    + populationWeight.doubleValue() * 10.0
                    + timeWeight * 5.0;

            int score = Math.max(1, Math.min(100, (int) Math.round(raw)));

            log.info("PriorityCalc done: alertEventCode={}, priorityScore={}",
                    alertEvent.getAlertEventCode(), score);

            return score;
        } catch (Exception e) {
            log.error("PriorityCalc error: alertEventCode={}", alertEvent.getAlertEventCode(), e);
            return 1;
        }
    }

    private int getLevelWeight(String alertLevel) {
        try {
            return AlertLevel.valueOf(alertLevel).getCode();
        } catch (Exception e) {
            return 1;
        }
    }

    private AreaPriority getAreaPriority(String areaId) {
        if (areaId == null) {
            return buildDefault();
        }
        try {
            AreaPriority ap = areaPriorityMapper.selectOne(
                    new LambdaQueryWrapper<AreaPriority>()
                            .eq(AreaPriority::getAreaId, areaId)
                            .last("LIMIT 1"));
            return ap != null ? ap : buildDefault();
        } catch (Exception e) {
            log.error("AreaPriority query failed: areaId={}", areaId, e);
            return buildDefault();
        }
    }

    private int getTimeWeight(Long eventTimestamp) {
        if (eventTimestamp == null) {
            return 2;
        }
        LocalTime time = LocalTime.ofInstant(
                Instant.ofEpochMilli(eventTimestamp), ZoneId.systemDefault());
        int hour = time.getHour();
        if (hour >= 22 || hour < 6) {
            return 5;
        }
        return 2;
    }

    private AreaPriority buildDefault() {
        AreaPriority ap = new AreaPriority();
        ap.setImportance(DEFAULT_IMPORTANCE);
        ap.setPopulationWeight(DEFAULT_POPULATION_WEIGHT);
        return ap;
    }
}
