package com.utc.alert.service.impl;

import com.utc.alert.dto.response.AreaPriorityResponse;
import com.utc.alert.entity.AreaPriority;
import com.utc.alert.mapper.AreaPriorityMapper;
import com.utc.alert.service.AreaPriorityService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class AreaPriorityServiceImpl implements AreaPriorityService {

    private final AreaPriorityMapper areaPriorityMapper;

    @Override
    public List<AreaPriorityResponse> getAllAreaPriorities() {
        List<AreaPriority> list = areaPriorityMapper.selectList(null);
        return list.stream()
                .map(this::toResponse)
                .collect(Collectors.toList());
    }

    private AreaPriorityResponse toResponse(AreaPriority area) {
        AreaPriorityResponse response = new AreaPriorityResponse();
        response.setId(area.getId());
        response.setAreaId(area.getAreaId());
        response.setAreaName(area.getAreaName());
        response.setImportance(area.getImportance());
        response.setPopulationWeight(area.getPopulationWeight());
        response.setDescription(area.getDescription());
        return response;
    }
}
