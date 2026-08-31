package com.utc.alert.service;

import com.utc.alert.dto.MatchResult;
import com.utc.alert.dto.kafka.KafkaMessage;
import com.utc.alert.dto.kafka.LocationInfo;
import com.utc.alert.entity.AlertRule;
import com.utc.alert.mapper.AlertRuleMapper;
import com.utc.alert.service.impl.RuleMatchServiceImpl;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.math.BigDecimal;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class RuleMatchServiceTest {

    @Mock
    private AlertRuleMapper alertRuleMapper;

    @InjectMocks
    private RuleMatchServiceImpl ruleMatchService;

    private AlertRule pressureRule;

    @BeforeEach
    void setUp() {
        pressureRule = new AlertRule();
        pressureRule.setRuleCode("RULE-PRESSURE-TEST");
        pressureRule.setRuleName("压力超限测试规则");
        pressureRule.setDeviceType("PRESSURE");
        pressureRule.setMetricKey("pressure");
        pressureRule.setAreaId(null);
        pressureRule.setBlueThreshold(new BigDecimal("2.0"));
        pressureRule.setYellowThreshold(new BigDecimal("3.0"));
        pressureRule.setOrangeThreshold(new BigDecimal("3.5"));
        pressureRule.setRedThreshold(new BigDecimal("4.0"));
        pressureRule.setCompareType("GT");
        pressureRule.setEnabled(true);
    }

    @Test
    void matchRules_pressureExceedsRedThreshold_returnsRed() {
        when(alertRuleMapper.selectMatchingRules(eq("PRESSURE"), eq("AREA-A01")))
                .thenReturn(List.of(pressureRule));

        KafkaMessage message = buildMessage("PRESSURE", "AREA-A01", "pressure", 4.5);

        List<MatchResult> results = ruleMatchService.matchRules(message);

        assertEquals(1, results.size());
        MatchResult result = results.get(0);
        assertEquals("RED", result.getAlertLevel());
        assertEquals("RULE-PRESSURE-TEST", result.getRuleCode());
        assertEquals("pressure", result.getMetricKey());
        assertEquals(new BigDecimal("4.5"), result.getMetricValue());
        assertEquals(new BigDecimal("4.0"), result.getThresholdValue());
    }

    @Test
    void matchRules_pressureExceedsOrangeThreshold_returnsOrange() {
        when(alertRuleMapper.selectMatchingRules(eq("PRESSURE"), eq("AREA-A01")))
                .thenReturn(List.of(pressureRule));

        KafkaMessage message = buildMessage("PRESSURE", "AREA-A01", "pressure", 3.6);

        List<MatchResult> results = ruleMatchService.matchRules(message);

        assertEquals(1, results.size());
        assertEquals("ORANGE", results.get(0).getAlertLevel());
    }

    @Test
    void matchRules_pressureExceedsBlueThreshold_returnsBlue() {
        when(alertRuleMapper.selectMatchingRules(eq("PRESSURE"), eq("AREA-A01")))
                .thenReturn(List.of(pressureRule));

        KafkaMessage message = buildMessage("PRESSURE", "AREA-A01", "pressure", 2.5);

        List<MatchResult> results = ruleMatchService.matchRules(message);

        assertEquals(1, results.size());
        assertEquals("BLUE", results.get(0).getAlertLevel());
    }

    @Test
    void matchRules_pressureBelowAllThresholds_returnsEmpty() {
        when(alertRuleMapper.selectMatchingRules(eq("PRESSURE"), eq("AREA-A01")))
                .thenReturn(List.of(pressureRule));

        KafkaMessage message = buildMessage("PRESSURE", "AREA-A01", "pressure", 1.0);

        List<MatchResult> results = ruleMatchService.matchRules(message);

        assertTrue(results.isEmpty());
    }

    @Test
    void matchRules_nullMessage_returnsEmpty() {
        List<MatchResult> results = ruleMatchService.matchRules(null);
        assertTrue(results.isEmpty());
    }

    @Test
    void matchRules_nullMetrics_returnsEmpty() {
        KafkaMessage message = new KafkaMessage();
        message.setDeviceType("PRESSURE");
        message.setMetrics(null);

        List<MatchResult> results = ruleMatchService.matchRules(message);
        assertTrue(results.isEmpty());
    }

    @Test
    void matchRules_noMatchingRules_returnsEmpty() {
        when(alertRuleMapper.selectMatchingRules(anyString(), anyString()))
                .thenReturn(Collections.emptyList());

        KafkaMessage message = buildMessage("TEMPERATURE", "AREA-A01", "temperature", 55.0);

        List<MatchResult> results = ruleMatchService.matchRules(message);
        assertTrue(results.isEmpty());
    }

    @Test
    void matchRules_metricKeyNotInRule_returnsEmpty() {
        when(alertRuleMapper.selectMatchingRules(eq("PRESSURE"), eq("AREA-A01")))
                .thenReturn(List.of(pressureRule));

        KafkaMessage message = buildMessage("PRESSURE", "AREA-A01", "temperature", 55.0);

        List<MatchResult> results = ruleMatchService.matchRules(message);
        assertTrue(results.isEmpty());
    }

    private KafkaMessage buildMessage(String deviceType, String areaId,
                                      String metricKey, double metricValue) {
        KafkaMessage message = new KafkaMessage();
        message.setEventId("test-event-001");
        message.setSource("test-service");
        message.setDeviceId("SENSOR-TEST-001");
        message.setDeviceType(deviceType);
        message.setTimestamp(System.currentTimeMillis());
        message.setEventType("SENSOR_DATA");

        LocationInfo location = new LocationInfo();
        location.setZone("ZONE-A01");
        location.setAreaId(areaId);
        message.setLocation(location);

        Map<String, Object> metrics = new HashMap<>();
        metrics.put(metricKey, metricValue);
        message.setMetrics(metrics);

        return message;
    }
}
