package com.utc.alert.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.utc.alert.common.ErrorCode;
import com.utc.alert.common.exception.BusinessException;
import com.utc.alert.dto.request.AlertRuleQueryRequest;
import com.utc.alert.dto.request.CreateAlertRuleRequest;
import com.utc.alert.dto.request.UpdateAlertRuleRequest;
import com.utc.alert.dto.response.AlertRuleResponse;
import com.utc.alert.dto.response.PageResponse;
import com.utc.alert.entity.AlertRule;
import com.utc.alert.mapper.AlertRuleMapper;
import com.utc.alert.service.AlertRuleService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.math.BigDecimal;
import java.util.List;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class AlertRuleServiceImpl implements AlertRuleService {

    private final AlertRuleMapper alertRuleMapper;

    @Override
    public PageResponse<AlertRuleResponse> getRules(AlertRuleQueryRequest request) {
        Page<AlertRule> page = new Page<>(request.getPage(), request.getSize());

        LambdaQueryWrapper<AlertRule> wrapper = new LambdaQueryWrapper<>();
        if (StringUtils.hasText(request.getRuleName())) {
            wrapper.like(AlertRule::getRuleName, request.getRuleName());
        }
        if (StringUtils.hasText(request.getDeviceType())) {
            wrapper.eq(AlertRule::getDeviceType, request.getDeviceType());
        }
        if (request.getEnabled() != null) {
            wrapper.eq(AlertRule::getEnabled, request.getEnabled());
        }
        wrapper.orderByDesc(AlertRule::getCreatedAt);

        Page<AlertRule> result = alertRuleMapper.selectPage(page, wrapper);

        List<AlertRuleResponse> records = result.getRecords().stream()
                .map(this::toResponse)
                .collect(Collectors.toList());

        return PageResponse.of(result, records);
    }

    @Override
    public AlertRuleResponse createRule(CreateAlertRuleRequest request) {
        validateThresholds(request.getBlueThreshold(), request.getYellowThreshold(),
                request.getOrangeThreshold(), request.getRedThreshold(), request.getCompareType());

        AlertRule rule = new AlertRule();
        rule.setRuleCode(request.getRuleCode());
        rule.setRuleName(request.getRuleName());
        rule.setDeviceType(request.getDeviceType());
        rule.setMetricKey(request.getMetricKey());
        rule.setAreaId(request.getAreaId());
        rule.setBlueThreshold(request.getBlueThreshold());
        rule.setYellowThreshold(request.getYellowThreshold());
        rule.setOrangeThreshold(request.getOrangeThreshold());
        rule.setRedThreshold(request.getRedThreshold());
        rule.setCompareType(request.getCompareType());
        rule.setEnabled(request.getEnabled());
        rule.setDescription(request.getDescription());

        alertRuleMapper.insert(rule);
        return toResponse(rule);
    }

    @Override
    public AlertRuleResponse updateRule(Long id, UpdateAlertRuleRequest request) {
        AlertRule rule = alertRuleMapper.selectById(id);
        if (rule == null) {
            throw new BusinessException(ErrorCode.RULE_NOT_FOUND);
        }

        validateThresholds(request.getBlueThreshold(), request.getYellowThreshold(),
                request.getOrangeThreshold(), request.getRedThreshold(), request.getCompareType());

        rule.setRuleName(request.getRuleName());
        rule.setDeviceType(request.getDeviceType());
        rule.setMetricKey(request.getMetricKey());
        rule.setAreaId(request.getAreaId());
        rule.setBlueThreshold(request.getBlueThreshold());
        rule.setYellowThreshold(request.getYellowThreshold());
        rule.setOrangeThreshold(request.getOrangeThreshold());
        rule.setRedThreshold(request.getRedThreshold());
        rule.setCompareType(request.getCompareType());
        if (request.getEnabled() != null) {
            rule.setEnabled(request.getEnabled());
        }
        rule.setDescription(request.getDescription());

        alertRuleMapper.updateById(rule);
        return toResponse(rule);
    }

    @Override
    public void deleteRule(Long id) {
        AlertRule rule = alertRuleMapper.selectById(id);
        if (rule == null) {
            throw new BusinessException(ErrorCode.RULE_NOT_FOUND);
        }
        alertRuleMapper.deleteById(id);
    }

    private void validateThresholds(BigDecimal blue, BigDecimal yellow,
                                    BigDecimal orange, BigDecimal red, String compareType) {
        if (blue == null || yellow == null || orange == null || red == null) {
            return;
        }

        if ("GT".equalsIgnoreCase(compareType) || "GTE".equalsIgnoreCase(compareType)) {
            if (!(red.compareTo(orange) >= 0 && orange.compareTo(yellow) >= 0
                    && yellow.compareTo(blue) >= 0)) {
                throw new BusinessException(ErrorCode.THRESHOLD_INVALID);
            }
        } else if ("LT".equalsIgnoreCase(compareType) || "LTE".equalsIgnoreCase(compareType)) {
            if (!(red.compareTo(orange) <= 0 && orange.compareTo(yellow) <= 0
                    && yellow.compareTo(blue) <= 0)) {
                throw new BusinessException(ErrorCode.THRESHOLD_INVALID);
            }
        }
    }

    private AlertRuleResponse toResponse(AlertRule rule) {
        AlertRuleResponse response = new AlertRuleResponse();
        response.setId(rule.getId());
        response.setRuleCode(rule.getRuleCode());
        response.setRuleName(rule.getRuleName());
        response.setDeviceType(rule.getDeviceType());
        response.setMetricKey(rule.getMetricKey());
        response.setAreaId(rule.getAreaId());
        response.setBlueThreshold(rule.getBlueThreshold());
        response.setYellowThreshold(rule.getYellowThreshold());
        response.setOrangeThreshold(rule.getOrangeThreshold());
        response.setRedThreshold(rule.getRedThreshold());
        response.setCompareType(rule.getCompareType());
        response.setEnabled(rule.getEnabled());
        response.setDescription(rule.getDescription());
        response.setCreatedAt(rule.getCreatedAt());
        response.setUpdatedAt(rule.getUpdatedAt());
        return response;
    }
}
