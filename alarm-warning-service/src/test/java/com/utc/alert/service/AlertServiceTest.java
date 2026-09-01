package com.utc.alert.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.utc.alert.common.exception.BusinessException;
import com.utc.alert.dto.request.AlertQueryRequest;
import com.utc.alert.dto.request.UpdateAlertStatusRequest;
import com.utc.alert.dto.response.AlertResponse;
import com.utc.alert.dto.response.PageResponse;
import com.utc.alert.entity.AlertEvent;
import com.utc.alert.mapper.AlertEventMapper;
import com.utc.alert.service.impl.AlertServiceImpl;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class AlertServiceTest {

    @Mock
    private AlertEventMapper alertEventMapper;

    @InjectMocks
    private AlertServiceImpl alertService;

    @Test
    void getAlerts_returnsPagedResults() {
        AlertEvent event = buildAlertEvent(1L, "RED", "OPEN");
        Page<AlertEvent> page = new Page<>(1, 10);
        page.setRecords(List.of(event));
        page.setTotal(1);
        when(alertEventMapper.selectPage(any(IPage.class), any())).thenReturn(page);

        AlertQueryRequest request = new AlertQueryRequest();
        request.setPage(1);
        request.setSize(10);

        PageResponse<AlertResponse> result = alertService.getAlerts(request);

        assertEquals(1, result.getRecords().size());
        assertEquals(1, result.getTotal());
        assertEquals("RED", result.getRecords().get(0).getAlertLevel());
    }

    @Test
    void getAlerts_withFilters_passesFiltersToQuery() {
        Page<AlertEvent> page = new Page<>(1, 10);
        page.setRecords(List.of());
        page.setTotal(0);
        when(alertEventMapper.selectPage(any(IPage.class), any())).thenReturn(page);

        AlertQueryRequest request = new AlertQueryRequest();
        request.setAlertLevel("RED");
        request.setStatus("OPEN");
        request.setAreaId("AREA-A01");

        alertService.getAlerts(request);

        verify(alertEventMapper).selectPage(any(IPage.class), any());
    }

    @Test
    void getAlertById_found_returnsResponse() {
        AlertEvent event = buildAlertEvent(1L, "RED", "OPEN");
        when(alertEventMapper.selectById(1L)).thenReturn(event);

        AlertResponse response = alertService.getAlertById(1L);

        assertEquals("RED", response.getAlertLevel());
        assertEquals("OPEN", response.getAlertStatus());
    }

    @Test
    void getAlertById_notFound_throwsBusinessException() {
        when(alertEventMapper.selectById(99L)).thenReturn(null);

        BusinessException ex = assertThrows(BusinessException.class,
                () -> alertService.getAlertById(99L));
        assertEquals(40204, ex.getCode());
    }

    @Test
    void updateAlertStatus_validTransition_succeeds() {
        AlertEvent event = buildAlertEvent(1L, "RED", "OPEN");
        when(alertEventMapper.selectById(1L)).thenReturn(event);
        when(alertEventMapper.updateById(any())).thenReturn(1);

        UpdateAlertStatusRequest request = new UpdateAlertStatusRequest();
        request.setStatus("ACKNOWLEDGED");

        AlertResponse response = alertService.updateAlertStatus(1L, request);

        assertEquals("ACKNOWLEDGED", response.getAlertStatus());
        verify(alertEventMapper).updateById(any());
    }

    @Test
    void updateAlertStatus_invalidTransition_throwsBusinessException() {
        AlertEvent event = buildAlertEvent(1L, "RED", "OPEN");
        when(alertEventMapper.selectById(1L)).thenReturn(event);

        UpdateAlertStatusRequest request = new UpdateAlertStatusRequest();
        request.setStatus("RESOLVED");

        BusinessException ex = assertThrows(BusinessException.class,
                () -> alertService.updateAlertStatus(1L, request));
        assertEquals(40205, ex.getCode());
    }

    @Test
    void updateAlertStatus_notFound_throwsBusinessException() {
        when(alertEventMapper.selectById(99L)).thenReturn(null);

        UpdateAlertStatusRequest request = new UpdateAlertStatusRequest();
        request.setStatus("ACKNOWLEDGED");

        BusinessException ex = assertThrows(BusinessException.class,
                () -> alertService.updateAlertStatus(99L, request));
        assertEquals(40204, ex.getCode());
    }

    @Test
    void updateAlertStatus_closedCannotTransition() {
        AlertEvent event = buildAlertEvent(1L, "RED", "CLOSED");
        when(alertEventMapper.selectById(1L)).thenReturn(event);

        UpdateAlertStatusRequest request = new UpdateAlertStatusRequest();
        request.setStatus("OPEN");

        assertThrows(BusinessException.class,
                () -> alertService.updateAlertStatus(1L, request));
    }

    private AlertEvent buildAlertEvent(Long id, String level, String status) {
        AlertEvent event = new AlertEvent();
        event.setId(id);
        event.setAlertEventCode("ALT-001");
        event.setSourceEventId("src-001");
        event.setSource("tunnel-service");
        event.setDeviceId("SENSOR-001");
        event.setDeviceType("PRESSURE");
        event.setZone("ZONE-A01");
        event.setAreaId("AREA-A01");
        event.setAlertLevel(level);
        event.setAlertStatus(status);
        event.setMetricKey("pressure");
        event.setPriorityScore(80);
        event.setMergedCount(1);
        event.setEventTimestamp(System.currentTimeMillis());
        return event;
    }
}
