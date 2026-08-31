package com.utc.alert.service;

import com.utc.alert.entity.AlertEvent;
import com.utc.alert.entity.AreaPriority;
import com.utc.alert.mapper.AreaPriorityMapper;
import com.utc.alert.service.impl.PriorityCalcServiceImpl;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalDate;
import java.time.LocalTime;
import java.time.ZoneId;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class PriorityCalcServiceTest {

    @Mock
    private AreaPriorityMapper areaPriorityMapper;

    @InjectMocks
    private PriorityCalcServiceImpl priorityCalcService;

    private AlertEvent buildEvent(String alertLevel, String areaId, Long timestamp) {
        AlertEvent event = new AlertEvent();
        event.setAlertEventCode("ALT-test-001");
        event.setAlertLevel(alertLevel);
        event.setAreaId(areaId);
        event.setEventTimestamp(timestamp);
        return event;
    }

    private AreaPriority buildAreaPriority(int importance, double populationWeight) {
        AreaPriority ap = new AreaPriority();
        ap.setAreaId("AREA-A01");
        ap.setImportance(importance);
        ap.setPopulationWeight(new BigDecimal(String.valueOf(populationWeight)));
        return ap;
    }

    private long nightTimestamp() {
        return LocalDate.of(2024, 9, 1)
                .atTime(LocalTime.of(23, 0))
                .atZone(ZoneId.systemDefault())
                .toInstant()
                .toEpochMilli();
    }

    private long dayTimestamp() {
        return LocalDate.of(2024, 9, 1)
                .atTime(LocalTime.of(14, 0))
                .atZone(ZoneId.systemDefault())
                .toInstant()
                .toEpochMilli();
    }

    @Test
    void calculate_redHighImportanceAreaNight_highScore() {
        AlertEvent event = buildEvent("RED", "AREA-A01", nightTimestamp());
        when(areaPriorityMapper.selectOne(any()))
                .thenReturn(buildAreaPriority(8, 1.5));

        int score = priorityCalcService.calculate(event);

        assertTrue(score > 80, "Expected score > 80 but got " + score);
        assertEquals(100, score);
    }

    @Test
    void calculate_blueLowImportanceAreaDay_lowerScore() {
        AlertEvent event = buildEvent("BLUE", "AREA-B02", dayTimestamp());
        when(areaPriorityMapper.selectOne(any()))
                .thenReturn(buildAreaPriority(2, 0.8));

        int score = priorityCalcService.calculate(event);

        assertEquals(68, score);
    }

    @Test
    void calculate_nullEvent_returnsMinimum() {
        assertEquals(1, priorityCalcService.calculate(null));
    }

    @Test
    void calculate_nullAreaId_usesDefaults() {
        AlertEvent event = buildEvent("YELLOW", null, dayTimestamp());

        int score = priorityCalcService.calculate(event);

        // YELLOW(2)*20 + default_importance(5)*15 + default_popWeight(1.0)*10 + day(2)*5
        // = 40 + 75 + 10 + 10 = 135 → clamped to 100
        assertEquals(100, score);
        verify(areaPriorityMapper, never()).selectOne(any());
    }

    @Test
    void calculate_areaNotFound_usesDefaults() {
        AlertEvent event = buildEvent("BLUE", "AREA-UNKNOWN", dayTimestamp());
        when(areaPriorityMapper.selectOne(any())).thenReturn(null);

        int score = priorityCalcService.calculate(event);

        // BLUE(1)*20 + 5*15 + 1.0*10 + 2*5 = 20+75+10+10 = 115 → 100
        assertEquals(100, score);
    }

    @Test
    void calculate_dbException_usesDefaults() {
        AlertEvent event = buildEvent("BLUE", "AREA-A01", dayTimestamp());
        when(areaPriorityMapper.selectOne(any())).thenThrow(new RuntimeException("DB down"));

        int score = priorityCalcService.calculate(event);

        assertEquals(100, score);
    }

    @Test
    void calculate_nullTimestamp_defaultsToDaytime() {
        AlertEvent event = buildEvent("BLUE", "AREA-A01", null);
        when(areaPriorityMapper.selectOne(any()))
                .thenReturn(buildAreaPriority(2, 0.8));

        int score = priorityCalcService.calculate(event);

        // BLUE(1)*20 + 2*15 + 0.8*10 + default_day(2)*5 = 20+30+8+10 = 68
        assertEquals(68, score);
    }

    @Test
    void calculate_invalidAlertLevel_defaultsToWeight1() {
        AlertEvent event = buildEvent("INVALID_LEVEL", "AREA-A01", dayTimestamp());
        when(areaPriorityMapper.selectOne(any()))
                .thenReturn(buildAreaPriority(5, 1.0));

        int score = priorityCalcService.calculate(event);

        // invalid(1)*20 + 5*15 + 1.0*10 + 2*5 = 20+75+10+10 = 115 → 100
        assertEquals(100, score);
    }
}
