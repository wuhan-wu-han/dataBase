package com.utc.alert.service;

import com.utc.alert.dto.MatchResult;
import com.utc.alert.dto.kafka.KafkaMessage;
import com.utc.alert.dto.kafka.LocationInfo;
import com.utc.alert.entity.AlertEvent;
import com.utc.alert.mapper.AlertEventMapper;
import com.utc.alert.service.impl.AlertEngineServiceImpl;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.math.BigDecimal;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class AlertEngineServiceTest {

    @Mock
    private RuleMatchService ruleMatchService;

    @Mock
    private AlertEventMapper alertEventMapper;

    @InjectMocks
    private AlertEngineServiceImpl alertEngineService;

    private KafkaMessage baseMessage;

    @BeforeEach
    void setUp() {
        baseMessage = new KafkaMessage();
        baseMessage.setEventId("tunnel-service-test-uuid-001");
        baseMessage.setSource("tunnel-service");
        baseMessage.setDeviceId("SENSOR-P-001");
        baseMessage.setDeviceType("PRESSURE");
        baseMessage.setTimestamp(1725100800000L);
        baseMessage.setEventType("SENSOR_DATA");

        LocationInfo location = new LocationInfo();
        location.setZone("ZONE-A01");
        location.setAreaId("AREA-A01");
        baseMessage.setLocation(location);

        Map<String, Object> metrics = new HashMap<>();
        metrics.put("pressure", 4.5);
        baseMessage.setMetrics(metrics);
    }

    @Test
    void processMessage_redLevelMatch_savesAlertEvent() {
        MatchResult redResult = buildMatchResult("RED", "RULE-P-001", "pressure",
                new BigDecimal("4.5"), new BigDecimal("4.0"));
        when(ruleMatchService.matchRules(any())).thenReturn(List.of(redResult));
        when(alertEventMapper.insert(any(AlertEvent.class))).thenReturn(1);

        alertEngineService.processMessage(baseMessage);

        ArgumentCaptor<AlertEvent> captor = ArgumentCaptor.forClass(AlertEvent.class);
        verify(alertEventMapper).insert(captor.capture());

        AlertEvent event = captor.getValue();
        assertTrue(event.getAlertEventCode().startsWith("ALT-"));
        assertEquals("tunnel-service-test-uuid-001", event.getSourceEventId());
        assertEquals("tunnel-service", event.getSource());
        assertEquals("SENSOR-P-001", event.getDeviceId());
        assertEquals("PRESSURE", event.getDeviceType());
        assertEquals("ZONE-A01", event.getZone());
        assertEquals("AREA-A01", event.getAreaId());
        assertEquals("RED", event.getAlertLevel());
        assertEquals("OPEN", event.getAlertStatus());
        assertEquals("pressure", event.getMetricKey());
        assertEquals(new BigDecimal("4.5"), event.getMetricValue());
        assertEquals(new BigDecimal("4.0"), event.getThresholdValue());
        assertEquals(1725100800000L, event.getEventTimestamp());
        assertEquals(0, event.getPriorityScore());
        assertEquals(1, event.getMergedCount());
    }

    @Test
    void processMessage_multipleMatches_selectsHighestLevel() {
        MatchResult blueResult = buildMatchResult("BLUE", "RULE-P-BLUE", "pressure",
                new BigDecimal("4.5"), new BigDecimal("2.0"));
        MatchResult redResult = buildMatchResult("RED", "RULE-P-RED", "pressure",
                new BigDecimal("4.5"), new BigDecimal("4.0"));

        when(ruleMatchService.matchRules(any())).thenReturn(List.of(blueResult, redResult));
        when(alertEventMapper.insert(any(AlertEvent.class))).thenReturn(1);

        alertEngineService.processMessage(baseMessage);

        ArgumentCaptor<AlertEvent> captor = ArgumentCaptor.forClass(AlertEvent.class);
        verify(alertEventMapper).insert(captor.capture());
        assertEquals("RED", captor.getValue().getAlertLevel());
    }

    @Test
    void processMessage_noMatch_doesNotSave() {
        when(ruleMatchService.matchRules(any())).thenReturn(Collections.emptyList());

        alertEngineService.processMessage(baseMessage);

        verify(alertEventMapper, never()).insert(any());
    }

    @Test
    void processMessage_nullMessage_doesNotThrow() {
        assertDoesNotThrow(() -> alertEngineService.processMessage(null));
        verify(ruleMatchService, never()).matchRules(any());
    }

    @Test
    void processMessage_missingEventId_skipsProcessing() {
        baseMessage.setEventId(null);

        alertEngineService.processMessage(baseMessage);

        verify(ruleMatchService, never()).matchRules(any());
        verify(alertEventMapper, never()).insert(any());
    }

    @Test
    void processMessage_missingSource_skipsProcessing() {
        baseMessage.setSource(null);

        alertEngineService.processMessage(baseMessage);

        verify(ruleMatchService, never()).matchRules(any());
    }

    @Test
    void processMessage_missingDeviceId_skipsProcessing() {
        baseMessage.setDeviceId(null);

        alertEngineService.processMessage(baseMessage);

        verify(ruleMatchService, never()).matchRules(any());
    }

    @Test
    void processMessage_missingTimestamp_skipsProcessing() {
        baseMessage.setTimestamp(null);

        alertEngineService.processMessage(baseMessage);

        verify(ruleMatchService, never()).matchRules(any());
    }

    @Test
    void processMessage_missingEventType_skipsProcessing() {
        baseMessage.setEventType(null);

        alertEngineService.processMessage(baseMessage);

        verify(ruleMatchService, never()).matchRules(any());
    }

    @Test
    void processMessage_dbException_doesNotThrow() {
        MatchResult result = buildMatchResult("RED", "RULE-P-001", "pressure",
                new BigDecimal("4.5"), new BigDecimal("4.0"));
        when(ruleMatchService.matchRules(any())).thenReturn(List.of(result));
        when(alertEventMapper.insert(any())).thenThrow(new RuntimeException("DB error"));

        assertDoesNotThrow(() -> alertEngineService.processMessage(baseMessage));
    }

    @Test
    void processMessage_ruleMatchException_doesNotThrow() {
        when(ruleMatchService.matchRules(any())).thenThrow(new RuntimeException("Rule engine error"));

        assertDoesNotThrow(() -> alertEngineService.processMessage(baseMessage));
        verify(alertEventMapper, never()).insert(any());
    }

    private MatchResult buildMatchResult(String level, String ruleCode, String metricKey,
                                         BigDecimal metricValue, BigDecimal thresholdValue) {
        MatchResult result = new MatchResult();
        result.setAlertLevel(level);
        result.setRuleCode(ruleCode);
        result.setRuleName("测试规则");
        result.setMetricKey(metricKey);
        result.setMetricValue(metricValue);
        result.setThresholdValue(thresholdValue);
        result.setDeviceType("PRESSURE");
        result.setAreaId("AREA-A01");
        return result;
    }
}
