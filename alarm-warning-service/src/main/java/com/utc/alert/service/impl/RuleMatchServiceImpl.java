package com.utc.alert.service.impl;

import com.utc.alert.common.enums.AlertLevel;
import com.utc.alert.dto.MatchResult;
import com.utc.alert.dto.kafka.KafkaMessage;
import com.utc.alert.dto.kafka.LocationInfo;
import com.utc.alert.entity.AlertRule;
import com.utc.alert.mapper.AlertRuleMapper;
import com.utc.alert.service.RuleMatchService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;

@Slf4j
@Service
@RequiredArgsConstructor
public class RuleMatchServiceImpl implements RuleMatchService {

    private final AlertRuleMapper alertRuleMapper;

    @Override
    public List<MatchResult> matchRules(KafkaMessage message) {
        if (message == null || message.getDeviceType() == null) {
            return Collections.emptyList();
        }

        Map<String, Object> metrics = message.getMetrics();
        if (metrics == null || metrics.isEmpty()) {
            return Collections.emptyList();
        }

        String deviceType = message.getDeviceType();
        String areaId = extractAreaId(message);

        List<AlertRule> rules;
        try {
            rules = alertRuleMapper.selectMatchingRules(deviceType, areaId);
        } catch (Exception e) {
            log.error("Failed to query alert rules, deviceType={}, areaId={}", deviceType, areaId, e);
            return Collections.emptyList();
        }

        if (rules == null || rules.isEmpty()) {
            return Collections.emptyList();
        }

        List<MatchResult> results = new ArrayList<>();
        for (AlertRule rule : rules) {
            MatchResult result = evaluateRule(rule, metrics, areaId);
            if (result != null) {
                results.add(result);
            }
        }

        return results;
    }

    private MatchResult evaluateRule(AlertRule rule, Map<String, Object> metrics, String areaId) {
        String metricKey = rule.getMetricKey();
        Object rawValue = metrics.get(metricKey);
        if (rawValue == null) {
            return null;
        }

        BigDecimal metricValue = toBigDecimal(rawValue);
        if (metricValue == null) {
            log.warn("Cannot parse metric value, metricKey={}, rawValue={}", metricKey, rawValue);
            return null;
        }

        AlertLevel level = determineLevel(metricValue, rule);
        if (level == null) {
            return null;
        }

        BigDecimal threshold = getThresholdForLevel(rule, level);

        MatchResult result = new MatchResult();
        result.setRuleCode(rule.getRuleCode());
        result.setRuleName(rule.getRuleName());
        result.setAlertLevel(level.name());
        result.setMetricKey(metricKey);
        result.setMetricValue(metricValue);
        result.setThresholdValue(threshold);
        result.setDeviceType(rule.getDeviceType());
        result.setAreaId(areaId);
        return result;
    }

    private AlertLevel determineLevel(BigDecimal value, AlertRule rule) {
        String compareType = rule.getCompareType();

        if (rule.getRedThreshold() != null && compare(value, rule.getRedThreshold(), compareType)) {
            return AlertLevel.RED;
        }
        if (rule.getOrangeThreshold() != null && compare(value, rule.getOrangeThreshold(), compareType)) {
            return AlertLevel.ORANGE;
        }
        if (rule.getYellowThreshold() != null && compare(value, rule.getYellowThreshold(), compareType)) {
            return AlertLevel.YELLOW;
        }
        if (rule.getBlueThreshold() != null && compare(value, rule.getBlueThreshold(), compareType)) {
            return AlertLevel.BLUE;
        }
        return null;
    }

    private boolean compare(BigDecimal value, BigDecimal threshold, String compareType) {
        if (compareType == null) {
            return false;
        }
        int cmp = value.compareTo(threshold);
        return switch (compareType) {
            case "GT" -> cmp > 0;
            case "GTE" -> cmp >= 0;
            case "LT" -> cmp < 0;
            case "LTE" -> cmp <= 0;
            case "EQ" -> cmp == 0;
            default -> false;
        };
    }

    private BigDecimal getThresholdForLevel(AlertRule rule, AlertLevel level) {
        return switch (level) {
            case RED -> rule.getRedThreshold();
            case ORANGE -> rule.getOrangeThreshold();
            case YELLOW -> rule.getYellowThreshold();
            case BLUE -> rule.getBlueThreshold();
        };
    }

    private String extractAreaId(KafkaMessage message) {
        LocationInfo location = message.getLocation();
        if (location != null && location.getAreaId() != null) {
            return location.getAreaId();
        }
        return null;
    }

    private BigDecimal toBigDecimal(Object value) {
        if (value instanceof BigDecimal bd) {
            return bd;
        }
        if (value instanceof Number num) {
            return BigDecimal.valueOf(num.doubleValue());
        }
        try {
            return new BigDecimal(value.toString());
        } catch (NumberFormatException e) {
            return null;
        }
    }
}
