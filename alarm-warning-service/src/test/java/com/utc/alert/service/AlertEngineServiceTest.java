package com.utc.alert.service;

import com.utc.alert.dto.MatchResult;
import com.utc.alert.dto.RootCauseResult;
import com.utc.alert.dto.kafka.KafkaMessage;
import com.utc.alert.dto.kafka.LocationInfo;
import com.utc.alert.entity.AlertEvent;
import com.utc.alert.entity.AlertGroup;
import com.utc.alert.mapper.AlertEventMapper;
import com.utc.alert.mapper.AlertGroupMapper;
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
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class AlertEngineServiceTest {

    @Mock
    private RuleMatchService ruleMatchService;

    @Mock
    private RootCauseService rootCauseService;

    @Mock
    private AlertDedupService alertDedupService;

    @Mock
    private PriorityCalcService priorityCalcService;

    @Mock
    private AlertEventMapper alertEventMapper;

    @Mock
    private AlertGroupMapper alertGroupMapper;

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

    private RootCauseResult buildRootCauseResult(String type, String desc) {
        RootCauseResult result = new RootCauseResult();
        result.setRootCauseType(type);
        result.setRootCauseDesc(desc);
        return result;
    }

    @Test
    void processMessage_redLevelMatch_savesAlertEvent() {
        MatchResult redResult = buildMatchResult("RED", "RULE-P-001", "pressure",
                new BigDecimal("4.5"), new BigDecimal("4.0"));
        when(ruleMatchService.matchRules(any())).thenReturn(List.of(redResult));
        when(rootCauseService.analyze(any()))
                .thenReturn(buildRootCauseResult("PRESSURE_ABNORMAL", "压力指标异常，需要检查管道压力状态。"));
        when(alertDedupService.tryMerge(any())).thenReturn(Optional.empty());
        AlertGroup newGroup = new AlertGroup();
        newGroup.setId(100L);
        newGroup.setAreaId("AREA-A01");
        newGroup.setTotalCount(1);
        when(alertGroupMapper.selectOne(any())).thenReturn(newGroup);
        when(priorityCalcService.calculate(any())).thenReturn(85);
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
        assertEquals("PRESSURE_ABNORMAL", event.getRootCause());
        assertEquals("压力指标异常，需要检查管道压力状态。", event.getRootCauseDesc());
        assertEquals(100L, event.getAlertGroupId());
        assertEquals(1725100800000L, event.getEventTimestamp());
        assertEquals(85, event.getPriorityScore());
        assertEquals(1, event.getMergedCount());
    }

    @Test
    void processMessage_multipleMatches_selectsHighestLevel() {
        MatchResult blueResult = buildMatchResult("BLUE", "RULE-P-BLUE", "pressure",
                new BigDecimal("4.5"), new BigDecimal("2.0"));
        MatchResult redResult = buildMatchResult("RED", "RULE-P-RED", "pressure",
                new BigDecimal("4.5"), new BigDecimal("4.0"));

        when(ruleMatchService.matchRules(any())).thenReturn(List.of(blueResult, redResult));
        when(rootCauseService.analyze(any()))
                .thenReturn(buildRootCauseResult("PRESSURE_ABNORMAL", "压力指标异常"));
        when(alertDedupService.tryMerge(any())).thenReturn(Optional.empty());
        when(priorityCalcService.calculate(any())).thenReturn(80);
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
        when(rootCauseService.analyze(any()))
                .thenReturn(buildRootCauseResult("PRESSURE_ABNORMAL", "压力指标异常"));
        when(alertDedupService.tryMerge(any())).thenReturn(Optional.empty());
        when(priorityCalcService.calculate(any())).thenReturn(75);
        when(alertEventMapper.insert(any())).thenThrow(new RuntimeException("DB error"));

        assertDoesNotThrow(() -> alertEngineService.processMessage(baseMessage));
    }

    @Test
    void processMessage_ruleMatchException_doesNotThrow() {
        when(ruleMatchService.matchRules(any())).thenThrow(new RuntimeException("Rule engine error"));

        assertDoesNotThrow(() -> alertEngineService.processMessage(baseMessage));
        verify(alertEventMapper, never()).insert(any());
    }

    @Test
    void processMessage_rootCauseException_stillSavesAlert() {
        MatchResult result = buildMatchResult("RED", "RULE-P-001", "pressure",
                new BigDecimal("4.5"), new BigDecimal("4.0"));
        when(ruleMatchService.matchRules(any())).thenReturn(List.of(result));
        when(rootCauseService.analyze(any())).thenThrow(new RuntimeException("Root cause error"));
        when(alertDedupService.tryMerge(any())).thenReturn(Optional.empty());
        when(priorityCalcService.calculate(any())).thenReturn(70);
        when(alertEventMapper.insert(any(AlertEvent.class))).thenReturn(1);

        alertEngineService.processMessage(baseMessage);

        ArgumentCaptor<AlertEvent> captor = ArgumentCaptor.forClass(AlertEvent.class);
        verify(alertEventMapper).insert(captor.capture());
        assertNull(captor.getValue().getRootCause());
        assertNull(captor.getValue().getRootCauseDesc());
    }

    @Test
    void processMessage_dedupMerge_setsGroupIdAndMergedCount() {
        MatchResult result = buildMatchResult("RED", "RULE-P-001", "pressure",
                new BigDecimal("4.5"), new BigDecimal("4.0"));
        when(ruleMatchService.matchRules(any())).thenReturn(List.of(result));
        when(rootCauseService.analyze(any()))
                .thenReturn(buildRootCauseResult("PRESSURE_ABNORMAL", "压力指标异常"));
        when(alertDedupService.tryMerge(any())).thenReturn(Optional.of(42L));
        AlertGroup existingGroup = new AlertGroup();
        existingGroup.setId(42L);
        existingGroup.setTotalCount(3);
        when(alertGroupMapper.selectById(42L)).thenReturn(existingGroup);
        when(priorityCalcService.calculate(any())).thenReturn(90);
        when(alertEventMapper.insert(any(AlertEvent.class))).thenReturn(1);

        alertEngineService.processMessage(baseMessage);

        ArgumentCaptor<AlertEvent> captor = ArgumentCaptor.forClass(AlertEvent.class);
        verify(alertEventMapper).insert(captor.capture());
        assertEquals(42L, captor.getValue().getAlertGroupId());
        assertEquals(3, captor.getValue().getMergedCount());
    }

    @Test
    void processMessage_dedupException_stillSavesAlert() {
        MatchResult result = buildMatchResult("RED", "RULE-P-001", "pressure",
                new BigDecimal("4.5"), new BigDecimal("4.0"));
        when(ruleMatchService.matchRules(any())).thenReturn(List.of(result));
        when(rootCauseService.analyze(any()))
                .thenReturn(buildRootCauseResult("PRESSURE_ABNORMAL", "压力指标异常"));
        when(alertDedupService.tryMerge(any())).thenThrow(new RuntimeException("Redis down"));
        when(priorityCalcService.calculate(any())).thenReturn(60);
        when(alertEventMapper.insert(any(AlertEvent.class))).thenReturn(1);

        alertEngineService.processMessage(baseMessage);

        ArgumentCaptor<AlertEvent> captor = ArgumentCaptor.forClass(AlertEvent.class);
        verify(alertEventMapper).insert(captor.capture());
        assertNull(captor.getValue().getAlertGroupId());
        assertEquals(1, captor.getValue().getMergedCount());
    }

    @Test
    void processMessage_priorityCalcException_savesAlertWithZeroScore() {
        MatchResult result = buildMatchResult("RED", "RULE-P-001", "pressure",
                new BigDecimal("4.5"), new BigDecimal("4.0"));
        when(ruleMatchService.matchRules(any())).thenReturn(List.of(result));
        when(rootCauseService.analyze(any()))
                .thenReturn(buildRootCauseResult("PRESSURE_ABNORMAL", "压力指标异常"));
        when(alertDedupService.tryMerge(any())).thenReturn(Optional.empty());
        when(priorityCalcService.calculate(any())).thenThrow(new RuntimeException("DB error"));
        when(alertEventMapper.insert(any(AlertEvent.class))).thenReturn(1);

        alertEngineService.processMessage(baseMessage);

        ArgumentCaptor<AlertEvent> captor = ArgumentCaptor.forClass(AlertEvent.class);
        verify(alertEventMapper).insert(captor.capture());
        assertEquals(0, captor.getValue().getPriorityScore());
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
