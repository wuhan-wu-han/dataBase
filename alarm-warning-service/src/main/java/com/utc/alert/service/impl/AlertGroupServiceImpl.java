package com.utc.alert.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.utc.alert.common.ErrorCode;
import com.utc.alert.common.exception.BusinessException;
import com.utc.alert.dto.request.AlertGroupQueryRequest;
import com.utc.alert.dto.response.AlertGroupResponse;
import com.utc.alert.dto.response.PageResponse;
import com.utc.alert.entity.AlertGroup;
import com.utc.alert.mapper.AlertGroupMapper;
import com.utc.alert.service.AlertGroupService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.util.List;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class AlertGroupServiceImpl implements AlertGroupService {

    private final AlertGroupMapper alertGroupMapper;

    @Override
    public PageResponse<AlertGroupResponse> getGroups(AlertGroupQueryRequest request) {
        Page<AlertGroup> page = new Page<>(request.getPage(), request.getSize());

        LambdaQueryWrapper<AlertGroup> wrapper = new LambdaQueryWrapper<>();
        if (StringUtils.hasText(request.getAreaId())) {
            wrapper.eq(AlertGroup::getAreaId, request.getAreaId());
        }
        wrapper.orderByDesc(AlertGroup::getCreatedAt);

        Page<AlertGroup> result = alertGroupMapper.selectPage(page, wrapper);

        List<AlertGroupResponse> records = result.getRecords().stream()
                .map(this::toResponse)
                .collect(Collectors.toList());

        return PageResponse.of(result, records);
    }

    @Override
    public AlertGroupResponse getGroupById(Long id) {
        AlertGroup group = alertGroupMapper.selectById(id);
        if (group == null) {
            throw new BusinessException(ErrorCode.EVENT_NOT_FOUND);
        }
        return toResponse(group);
    }

    private AlertGroupResponse toResponse(AlertGroup group) {
        AlertGroupResponse response = new AlertGroupResponse();
        response.setId(group.getId());
        response.setGroupCode(group.getGroupCode());
        response.setAreaId(group.getAreaId());
        response.setZone(group.getZone());
        response.setHighestLevel(group.getHighestLevel());
        response.setTotalCount(group.getTotalCount());
        response.setGroupStatus(group.getGroupStatus());
        response.setWindowStart(group.getWindowStart());
        response.setWindowEnd(group.getWindowEnd());
        response.setCreatedAt(group.getCreatedAt());
        response.setUpdatedAt(group.getUpdatedAt());
        return response;
    }
}
