package com.utc.alert.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.utc.alert.common.exception.BusinessException;
import com.utc.alert.dto.request.AlertRuleQueryRequest;
import com.utc.alert.dto.request.CreateAlertRuleRequest;
import com.utc.alert.dto.request.UpdateAlertRuleRequest;
import com.utc.alert.dto.response.AlertRuleResponse;
import com.utc.alert.dto.response.PageResponse;
import com.utc.alert.entity.AlertRule;
import com.utc.alert.mapper.AlertRuleMapper;
import com.utc.alert.service.impl.AlertRuleServiceImpl;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.math.BigDecimal;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class AlertRuleServiceTest {

    @Mock
    private AlertRuleMapper alertRuleMapper;

    @InjectMocks
    private AlertRuleServiceImpl alertRuleService;

    @Test
    void getRules_returnsPagedResults() {
        AlertRule rule = buildAlertRule(1L, "RULE-001");
        Page<AlertRule> page = new Page<>(1, 10);
        page.setRecords(List.of(rule));
        page.setTotal(1);
        when(alertRuleMapper.selectPage(any(IPage.class), any())).thenReturn(page);

        AlertRuleQueryRequest request = new AlertRuleQueryRequest();
        PageResponse<AlertRuleResponse> result = alertRuleService.getRules(request);

        assertEquals(1, result.getRecords().size());
        assertEquals("RULE-001", result.getRecords().get(0).getRuleCode());
    }

    @Test
    void createRule_validRequest_succeeds() {
        when(alertRuleMapper.insert(any())).thenReturn(1);

        CreateAlertRuleRequest request = new CreateAlertRuleRequest();
        request.setRuleCode("RULE-NEW");
        request.setRuleName("压力规则");
        request.setDeviceType("PRESSURE");
        request.setMetricKey("pressure");
        request.setCompareType("GT");
        request.setBlueThreshold(new BigDecimal("1.0"));
        request.setYellowThreshold(new BigDecimal("2.0"));
        request.setOrangeThreshold(new BigDecimal("3.0"));
        request.setRedThreshold(new BigDecimal("4.0"));

        AlertRuleResponse response = alertRuleService.createRule(request);

        assertEquals("RULE-NEW", response.getRuleCode());
        verify(alertRuleMapper).insert(any());
    }

    @Test
    void createRule_invalidThresholds_throwsBusinessException() {
        CreateAlertRuleRequest request = new CreateAlertRuleRequest();
        request.setRuleCode("RULE-BAD");
        request.setRuleName("坏规则");
        request.setDeviceType("PRESSURE");
        request.setMetricKey("pressure");
        request.setCompareType("GT");
        request.setBlueThreshold(new BigDecimal("4.0"));
        request.setYellowThreshold(new BigDecimal("3.0"));
        request.setOrangeThreshold(new BigDecimal("2.0"));
        request.setRedThreshold(new BigDecimal("1.0"));

        BusinessException ex = assertThrows(BusinessException.class,
                () -> alertRuleService.createRule(request));
        assertEquals(40203, ex.getCode());
    }

    @Test
    void createRule_ltCompareType_validOrder() {
        when(alertRuleMapper.insert(any())).thenReturn(1);

        CreateAlertRuleRequest request = new CreateAlertRuleRequest();
        request.setRuleCode("RULE-LT");
        request.setRuleName("LT规则");
        request.setDeviceType("TEMP");
        request.setMetricKey("temperature");
        request.setCompareType("LT");
        request.setBlueThreshold(new BigDecimal("4.0"));
        request.setYellowThreshold(new BigDecimal("3.0"));
        request.setOrangeThreshold(new BigDecimal("2.0"));
        request.setRedThreshold(new BigDecimal("1.0"));

        AlertRuleResponse response = alertRuleService.createRule(request);
        assertEquals("RULE-LT", response.getRuleCode());
    }

    @Test
    void updateRule_found_succeeds() {
        AlertRule existing = buildAlertRule(1L, "RULE-001");
        when(alertRuleMapper.selectById(1L)).thenReturn(existing);
        when(alertRuleMapper.updateById(any())).thenReturn(1);

        UpdateAlertRuleRequest request = new UpdateAlertRuleRequest();
        request.setRuleName("更新规则");
        request.setDeviceType("PRESSURE");
        request.setMetricKey("pressure");
        request.setCompareType("GT");
        request.setBlueThreshold(new BigDecimal("1.0"));
        request.setYellowThreshold(new BigDecimal("2.0"));
        request.setOrangeThreshold(new BigDecimal("3.0"));
        request.setRedThreshold(new BigDecimal("4.0"));

        AlertRuleResponse response = alertRuleService.updateRule(1L, request);

        assertEquals("更新规则", response.getRuleName());
    }

    @Test
    void updateRule_notFound_throwsBusinessException() {
        when(alertRuleMapper.selectById(99L)).thenReturn(null);

        UpdateAlertRuleRequest request = new UpdateAlertRuleRequest();
        request.setRuleName("x");
        request.setDeviceType("x");
        request.setMetricKey("x");
        request.setCompareType("GT");

        BusinessException ex = assertThrows(BusinessException.class,
                () -> alertRuleService.updateRule(99L, request));
        assertEquals(40201, ex.getCode());
    }

    @Test
    void deleteRule_found_succeeds() {
        AlertRule existing = buildAlertRule(1L, "RULE-001");
        when(alertRuleMapper.selectById(1L)).thenReturn(existing);
        when(alertRuleMapper.deleteById(1L)).thenReturn(1);

        assertDoesNotThrow(() -> alertRuleService.deleteRule(1L));
        verify(alertRuleMapper).deleteById(1L);
    }

    @Test
    void deleteRule_notFound_throwsBusinessException() {
        when(alertRuleMapper.selectById(99L)).thenReturn(null);

        BusinessException ex = assertThrows(BusinessException.class,
                () -> alertRuleService.deleteRule(99L));
        assertEquals(40201, ex.getCode());
    }

    private AlertRule buildAlertRule(Long id, String ruleCode) {
        AlertRule rule = new AlertRule();
        rule.setId(id);
        rule.setRuleCode(ruleCode);
        rule.setRuleName("测试规则");
        rule.setDeviceType("PRESSURE");
        rule.setMetricKey("pressure");
        rule.setCompareType("GT");
        rule.setEnabled(true);
        return rule;
    }
}
