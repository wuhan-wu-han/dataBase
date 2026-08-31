package com.utc.alert.service;

import com.utc.alert.dto.RootCauseResult;
import com.utc.alert.dto.kafka.KafkaMessage;
import com.utc.alert.service.impl.RootCauseServiceImpl;
import org.junit.jupiter.api.Test;

import java.util.HashMap;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

class RootCauseServiceTest {

    private final RootCauseService rootCauseService = new RootCauseServiceImpl();

    @Test
    void analyze_pressureDeviceWithPressureMetric_returnsPressureAbnormal() {
        KafkaMessage message = buildMessage("PRESSURE", Map.of("pressure", 4.5));

        RootCauseResult result = rootCauseService.analyze(message);

        assertEquals("PRESSURE_ABNORMAL", result.getRootCauseType());
        assertNotNull(result.getRootCauseDesc());
        assertTrue(result.getRootCauseDesc().contains("压力"));
    }

    @Test
    void analyze_ch4DeviceWithCh4Concentration_returnsGasLeak() {
        KafkaMessage message = buildMessage("CH4", Map.of("ch4_concentration", 3.5));

        RootCauseResult result = rootCauseService.analyze(message);

        assertEquals("GAS_LEAK", result.getRootCauseType());
        assertNotNull(result.getRootCauseDesc());
        assertTrue(result.getRootCauseDesc().contains("泄漏"));
    }

    @Test
    void analyze_ch4DeviceWithCh4Key_returnsGasLeak() {
        KafkaMessage message = buildMessage("CH4", Map.of("ch4", 2.0));

        RootCauseResult result = rootCauseService.analyze(message);

        assertEquals("GAS_LEAK", result.getRootCauseType());
    }

    @Test
    void analyze_temperatureDeviceWithTemperatureMetric_returnsTemperatureAbnormal() {
        KafkaMessage message = buildMessage("TEMPERATURE", Map.of("temperature", 85.0));

        RootCauseResult result = rootCauseService.analyze(message);

        assertEquals("TEMPERATURE_ABNORMAL", result.getRootCauseType());
        assertTrue(result.getRootCauseDesc().contains("温度"));
    }

    @Test
    void analyze_h2sDevice_returnsGasLeak() {
        KafkaMessage message = buildMessage("H2S", Map.of("h2s", 10.0));

        RootCauseResult result = rootCauseService.analyze(message);

        assertEquals("GAS_LEAK", result.getRootCauseType());
        assertTrue(result.getRootCauseDesc().contains("硫化氢"));
    }

    @Test
    void analyze_unknownDeviceType_returnsUnknown() {
        KafkaMessage message = buildMessage("FLOW", Map.of("flow_rate", 100.0));

        RootCauseResult result = rootCauseService.analyze(message);

        assertEquals("UNKNOWN", result.getRootCauseType());
    }

    @Test
    void analyze_nullMessage_returnsUnknown() {
        RootCauseResult result = rootCauseService.analyze(null);

        assertEquals("UNKNOWN", result.getRootCauseType());
    }

    @Test
    void analyze_nullMetrics_returnsUnknown() {
        KafkaMessage message = buildMessage("PRESSURE", null);

        RootCauseResult result = rootCauseService.analyze(message);

        assertEquals("UNKNOWN", result.getRootCauseType());
    }

    @Test
    void analyze_emptyMetrics_returnsUnknown() {
        KafkaMessage message = buildMessage("PRESSURE", Map.of());

        RootCauseResult result = rootCauseService.analyze(message);

        assertEquals("UNKNOWN", result.getRootCauseType());
    }

    @Test
    void analyze_pressureDeviceWithoutPressureMetric_returnsUnknown() {
        KafkaMessage message = buildMessage("PRESSURE", Map.of("temperature", 50.0));

        RootCauseResult result = rootCauseService.analyze(message);

        assertEquals("UNKNOWN", result.getRootCauseType());
    }

    private KafkaMessage buildMessage(String deviceType, Map<String, Object> metrics) {
        KafkaMessage message = new KafkaMessage();
        message.setEventId("test-event-001");
        message.setSource("tunnel-service");
        message.setDeviceId("SENSOR-001");
        message.setDeviceType(deviceType);
        message.setTimestamp(System.currentTimeMillis());
        message.setEventType("SENSOR_DATA");
        if (metrics != null) {
            message.setMetrics(new HashMap<>(metrics));
        }
        return message;
    }
}
