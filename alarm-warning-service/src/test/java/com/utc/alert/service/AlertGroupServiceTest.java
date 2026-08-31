package com.utc.alert.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.utc.alert.common.exception.BusinessException;
import com.utc.alert.dto.request.AlertGroupQueryRequest;
import com.utc.alert.dto.response.AlertGroupResponse;
import com.utc.alert.dto.response.PageResponse;
import com.utc.alert.entity.AlertGroup;
import com.utc.alert.mapper.AlertGroupMapper;
import com.utc.alert.service.impl.AlertGroupServiceImpl;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class AlertGroupServiceTest {

    @Mock
    private AlertGroupMapper alertGroupMapper;

    @InjectMocks
    private AlertGroupServiceImpl alertGroupService;

    @Test
    void getGroups_returnsPagedResults() {
        AlertGroup group = buildAlertGroup(1L, "AREA-A01");
        Page<AlertGroup> page = new Page<>(1, 10);
        page.setRecords(List.of(group));
        page.setTotal(1);
        when(alertGroupMapper.selectPage(any(IPage.class), any())).thenReturn(page);

        AlertGroupQueryRequest request = new AlertGroupQueryRequest();
        PageResponse<AlertGroupResponse> result = alertGroupService.getGroups(request);

        assertEquals(1, result.getRecords().size());
        assertEquals("AREA-A01", result.getRecords().get(0).getAreaId());
    }

    @Test
    void getGroupById_found_returnsResponse() {
        AlertGroup group = buildAlertGroup(1L, "AREA-A01");
        when(alertGroupMapper.selectById(1L)).thenReturn(group);

        AlertGroupResponse response = alertGroupService.getGroupById(1L);

        assertEquals("AREA-A01", response.getAreaId());
        assertEquals("GRP-001", response.getGroupCode());
    }

    @Test
    void getGroupById_notFound_throwsBusinessException() {
        when(alertGroupMapper.selectById(99L)).thenReturn(null);

        BusinessException ex = assertThrows(BusinessException.class,
                () -> alertGroupService.getGroupById(99L));
        assertEquals(40204, ex.getCode());
    }

    private AlertGroup buildAlertGroup(Long id, String areaId) {
        AlertGroup group = new AlertGroup();
        group.setId(id);
        group.setGroupCode("GRP-001");
        group.setAreaId(areaId);
        group.setZone("ZONE-A01");
        group.setHighestLevel("RED");
        group.setTotalCount(5);
        group.setGroupStatus("ACTIVE");
        return group;
    }
}
