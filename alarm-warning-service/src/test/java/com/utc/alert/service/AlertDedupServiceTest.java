package com.utc.alert.service;

import com.utc.alert.entity.AlertEvent;
import com.utc.alert.entity.AlertGroup;
import com.utc.alert.mapper.AlertGroupMapper;
import com.utc.alert.service.impl.AlertDedupServiceImpl;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.ZSetOperations;
import org.springframework.test.util.ReflectionTestUtils;

import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class AlertDedupServiceTest {

    @Mock
    private StringRedisTemplate redisTemplate;

    @Mock
    private AlertGroupMapper alertGroupMapper;

    @Mock
    private ZSetOperations<String, String> zSetOperations;

    @InjectMocks
    private AlertDedupServiceImpl alertDedupService;

    @BeforeEach
    void setUp() {
        ReflectionTestUtils.setField(alertDedupService, "windowMinutes", 10);
        lenient().when(redisTemplate.opsForZSet()).thenReturn(zSetOperations);
    }

    @Test
    void tryMerge_existingWindow_mergesIntoGroup() {
        AlertEvent event = buildAlertEvent("AREA-A01", "RED", 1725100800000L);

        when(zSetOperations.removeRangeByScore(anyString(), anyDouble(), anyDouble())).thenReturn(0L);
        when(zSetOperations.zCard("alert:window:AREA-A01")).thenReturn(1L);

        AlertGroup existingGroup = new AlertGroup();
        existingGroup.setId(10L);
        existingGroup.setAreaId("AREA-A01");
        existingGroup.setHighestLevel("YELLOW");
        existingGroup.setTotalCount(1);
        when(alertGroupMapper.selectOne(any())).thenReturn(existingGroup);
        when(alertGroupMapper.updateById(any())).thenReturn(1);
        when(zSetOperations.add(anyString(), anyString(), anyDouble())).thenReturn(true);

        Optional<Long> result = alertDedupService.tryMerge(event);

        assertTrue(result.isPresent());
        assertEquals(10L, result.get());

        ArgumentCaptor<AlertGroup> groupCaptor = ArgumentCaptor.forClass(AlertGroup.class);
        verify(alertGroupMapper).updateById(groupCaptor.capture());
        AlertGroup updated = groupCaptor.getValue();
        assertEquals(2, updated.getTotalCount());
        assertEquals("RED", updated.getHighestLevel());

        verify(zSetOperations).add("alert:window:AREA-A01", event.getAlertEventCode(), 1725100800000.0);
    }

    @Test
    void tryMerge_existingWindow_keepsHigherLevel() {
        AlertEvent event = buildAlertEvent("AREA-A01", "BLUE", 1725100800000L);

        when(zSetOperations.removeRangeByScore(anyString(), anyDouble(), anyDouble())).thenReturn(0L);
        when(zSetOperations.zCard("alert:window:AREA-A01")).thenReturn(1L);

        AlertGroup existingGroup = new AlertGroup();
        existingGroup.setId(10L);
        existingGroup.setAreaId("AREA-A01");
        existingGroup.setHighestLevel("RED");
        existingGroup.setTotalCount(1);
        when(alertGroupMapper.selectOne(any())).thenReturn(existingGroup);
        when(alertGroupMapper.updateById(any())).thenReturn(1);
        when(zSetOperations.add(anyString(), anyString(), anyDouble())).thenReturn(true);

        alertDedupService.tryMerge(event);

        ArgumentCaptor<AlertGroup> captor = ArgumentCaptor.forClass(AlertGroup.class);
        verify(alertGroupMapper).updateById(captor.capture());
        assertEquals("RED", captor.getValue().getHighestLevel());
        assertEquals(2, captor.getValue().getTotalCount());
    }

    @Test
    void tryMerge_emptyWindow_createsNewGroup() {
        AlertEvent event = buildAlertEvent("AREA-A02", "RED", 1725100800000L);

        when(zSetOperations.removeRangeByScore(anyString(), anyDouble(), anyDouble())).thenReturn(0L);
        when(zSetOperations.zCard("alert:window:AREA-A02")).thenReturn(0L);
        when(alertGroupMapper.insert(any())).thenReturn(1);
        when(zSetOperations.add(anyString(), anyString(), anyDouble())).thenReturn(true);

        Optional<Long> result = alertDedupService.tryMerge(event);

        assertFalse(result.isPresent());

        ArgumentCaptor<AlertGroup> groupCaptor = ArgumentCaptor.forClass(AlertGroup.class);
        verify(alertGroupMapper).insert(groupCaptor.capture());
        AlertGroup newGroup = groupCaptor.getValue();
        assertEquals("AREA-A02", newGroup.getAreaId());
        assertEquals("RED", newGroup.getHighestLevel());
        assertEquals(1, newGroup.getTotalCount());
        assertEquals("ACTIVE", newGroup.getGroupStatus());
        assertTrue(newGroup.getGroupCode().startsWith("GRP-"));

        verify(zSetOperations).add("alert:window:AREA-A02", event.getAlertEventCode(), 1725100800000.0);
    }

    @Test
    void tryMerge_redisFailure_returnsEmpty() {
        AlertEvent event = buildAlertEvent("AREA-A01", "RED", 1725100800000L);

        when(zSetOperations.removeRangeByScore(anyString(), anyDouble(), anyDouble()))
                .thenThrow(new RuntimeException("Redis connection refused"));

        Optional<Long> result = alertDedupService.tryMerge(event);

        assertFalse(result.isPresent());
        verify(alertGroupMapper, never()).insert(any());
        verify(alertGroupMapper, never()).updateById(any());
    }

    @Test
    void tryMerge_nullEvent_returnsEmpty() {
        Optional<Long> result = alertDedupService.tryMerge(null);

        assertFalse(result.isPresent());
    }

    @Test
    void tryMerge_nullAreaId_returnsEmpty() {
        AlertEvent event = buildAlertEvent(null, "RED", 1725100800000L);

        Optional<Long> result = alertDedupService.tryMerge(event);

        assertFalse(result.isPresent());
    }

    @Test
    void tryMerge_existingWindow_groupNotFound_createsNewGroup() {
        AlertEvent event = buildAlertEvent("AREA-A01", "RED", 1725100800000L);

        when(zSetOperations.removeRangeByScore(anyString(), anyDouble(), anyDouble())).thenReturn(0L);
        when(zSetOperations.zCard("alert:window:AREA-A01")).thenReturn(1L);
        when(alertGroupMapper.selectOne(any())).thenReturn(null);
        when(alertGroupMapper.insert(any())).thenReturn(1);
        when(zSetOperations.add(anyString(), anyString(), anyDouble())).thenReturn(true);

        Optional<Long> result = alertDedupService.tryMerge(event);

        assertFalse(result.isPresent());
        verify(alertGroupMapper).insert(any());
    }

    @Test
    void tryMerge_sameAreaSecondAlert_groupCountBecomesTwo() {
        when(zSetOperations.removeRangeByScore(anyString(), anyDouble(), anyDouble())).thenReturn(0L);
        when(zSetOperations.add(anyString(), anyString(), anyDouble())).thenReturn(true);

        when(zSetOperations.zCard("alert:window:AREA-A01")).thenReturn(0L, 1L);
        when(alertGroupMapper.insert(any())).thenReturn(1);

        AlertEvent first = buildAlertEvent("AREA-A01", "RED", 1725100800000L);
        Optional<Long> firstResult = alertDedupService.tryMerge(first);
        assertFalse(firstResult.isPresent());

        AlertGroup existingGroup = new AlertGroup();
        existingGroup.setId(10L);
        existingGroup.setAreaId("AREA-A01");
        existingGroup.setHighestLevel("RED");
        existingGroup.setTotalCount(1);
        when(alertGroupMapper.selectOne(any())).thenReturn(existingGroup);
        when(alertGroupMapper.updateById(any())).thenReturn(1);

        AlertEvent second = buildAlertEvent("AREA-A01", "RED", 1725100800300000L);
        Optional<Long> secondResult = alertDedupService.tryMerge(second);

        assertTrue(secondResult.isPresent());
        assertEquals(10L, secondResult.get());

        ArgumentCaptor<AlertGroup> captor = ArgumentCaptor.forClass(AlertGroup.class);
        verify(alertGroupMapper).updateById(captor.capture());
        assertEquals(2, captor.getValue().getTotalCount());
    }

    private AlertEvent buildAlertEvent(String areaId, String alertLevel, long timestamp) {
        AlertEvent event = new AlertEvent();
        event.setAlertEventCode("ALT-test-uuid");
        event.setDeviceId("SENSOR-P-001");
        event.setDeviceType("PRESSURE");
        event.setZone("ZONE-A01");
        event.setAreaId(areaId);
        event.setAlertLevel(alertLevel);
        event.setEventTimestamp(timestamp);
        return event;
    }
}
