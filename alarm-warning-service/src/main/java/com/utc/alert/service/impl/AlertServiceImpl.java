package com.utc.alert.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.utc.alert.common.ErrorCode;
import com.utc.alert.common.enums.AlertStatus;
import com.utc.alert.common.exception.BusinessException;
import com.utc.alert.dto.request.AlertQueryRequest;
import com.utc.alert.dto.request.UpdateAlertStatusRequest;
import com.utc.alert.dto.response.AlertResponse;
import com.utc.alert.dto.response.PageResponse;
import com.utc.alert.entity.AlertEvent;
import com.utc.alert.mapper.AlertEventMapper;
import com.utc.alert.service.AlertService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class AlertServiceImpl implements AlertService {

    private static final Map<String, Set<String>> VALID_TRANSITIONS = Map.of(
            "OPEN", Set.of("ACKNOWLEDGED"),
            "ACKNOWLEDGED", Set.of("RESOLVED"),
            "RESOLVED", Set.of("CLOSED")
    );

    private final AlertEventMapper alertEventMapper;

    @Override
    public PageResponse<AlertResponse> getAlerts(AlertQueryRequest request) {
        Page<AlertEvent> page = new Page<>(request.getPage(), request.getSize());

        LambdaQueryWrapper<AlertEvent> wrapper = new LambdaQueryWrapper<>();
        if (StringUtils.hasText(request.getAlertLevel())) {
            wrapper.eq(AlertEvent::getAlertLevel, request.getAlertLevel());
        }
        if (StringUtils.hasText(request.getStatus())) {
            wrapper.eq(AlertEvent::getAlertStatus, request.getStatus());
        }
        if (StringUtils.hasText(request.getAreaId())) {
            wrapper.eq(AlertEvent::getAreaId, request.getAreaId());
        }
        wrapper.orderByDesc(AlertEvent::getCreatedAt);

        Page<AlertEvent> result = alertEventMapper.selectPage(page, wrapper);

        List<AlertResponse> records = result.getRecords().stream()
                .map(this::toResponse)
                .collect(Collectors.toList());

        return PageResponse.of(result, records);
    }

    @Override
    public AlertResponse getAlertById(Long id) {
        AlertEvent event = alertEventMapper.selectById(id);
        if (event == null) {
            throw new BusinessException(ErrorCode.EVENT_NOT_FOUND);
        }
        return toResponse(event);
    }

    @Override
    public AlertResponse updateAlertStatus(Long id, UpdateAlertStatusRequest request) {
        AlertEvent event = alertEventMapper.selectById(id);
        if (event == null) {
            throw new BusinessException(ErrorCode.EVENT_NOT_FOUND);
        }

        String currentStatus = event.getAlertStatus();
        String newStatus = request.getStatus();

        Set<String> allowed = VALID_TRANSITIONS.get(currentStatus);
        if (allowed == null || !allowed.contains(newStatus)) {
            throw new BusinessException(ErrorCode.ILLEGAL_STATUS_TRANSITION);
        }

        event.setAlertStatus(newStatus);
        alertEventMapper.updateById(event);

        return toResponse(event);
    }

    private AlertResponse toResponse(AlertEvent event) {
        AlertResponse response = new AlertResponse();
        response.setId(event.getId());
        response.setAlertEventCode(event.getAlertEventCode());
        response.setSourceEventId(event.getSourceEventId());
        response.setSource(event.getSource());
        response.setDeviceId(event.getDeviceId());
        response.setDeviceType(event.getDeviceType());
        response.setZone(event.getZone());
        response.setAreaId(event.getAreaId());
        response.setAlertLevel(event.getAlertLevel());
        response.setAlertStatus(event.getAlertStatus());
        response.setMetricKey(event.getMetricKey());
        response.setMetricValue(event.getMetricValue());
        response.setThresholdValue(event.getThresholdValue());
        response.setRootCause(event.getRootCause());
        response.setRootCauseDesc(event.getRootCauseDesc());
        response.setPriorityScore(event.getPriorityScore());
        response.setAlertGroupId(event.getAlertGroupId());
        response.setMergedCount(event.getMergedCount());
        response.setEventTimestamp(event.getEventTimestamp());
        response.setCreatedAt(event.getCreatedAt());
        response.setUpdatedAt(event.getUpdatedAt());
        return response;
    }
}
