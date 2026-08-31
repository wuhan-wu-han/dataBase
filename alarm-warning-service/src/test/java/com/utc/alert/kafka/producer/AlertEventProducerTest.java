package com.utc.alert.kafka.producer;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.utc.alert.entity.AlertEvent;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Spy;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.support.SendResult;
import org.springframework.test.util.ReflectionTestUtils;

import java.util.concurrent.CompletableFuture;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class AlertEventProducerTest {

    @Mock
    private KafkaTemplate<String, String> kafkaTemplate;

    @Spy
    private ObjectMapper objectMapper = new ObjectMapper();

    @InjectMocks
    private AlertEventProducer alertEventProducer;

    private AlertEvent testEvent;

    @BeforeEach
    void setUp() {
        ReflectionTestUtils.setField(alertEventProducer, "topic", "alert-event-topic");

        testEvent = new AlertEvent();
        testEvent.setAlertEventCode("ALT-test-001");
        testEvent.setDeviceId("SENSOR-P-001");
        testEvent.setDeviceType("PRESSURE");
        testEvent.setAreaId("AREA-A01");
        testEvent.setAlertLevel("RED");
        testEvent.setAlertStatus("OPEN");
        testEvent.setRootCause("PRESSURE_ABNORMAL");
        testEvent.setPriorityScore(95);
        testEvent.setMergedCount(1);
    }

    @Test
    void send_constructsKafkaMessageAndPublishes() throws Exception {
        CompletableFuture future = CompletableFuture.completedFuture(null);
        when(kafkaTemplate.send(eq("alert-event-topic"), anyString(), anyString()))
                .thenReturn(future);

        alertEventProducer.send(testEvent);

        ArgumentCaptor<String> keyCaptor = ArgumentCaptor.forClass(String.class);
        ArgumentCaptor<String> valueCaptor = ArgumentCaptor.forClass(String.class);
        verify(kafkaTemplate).send(eq("alert-event-topic"), keyCaptor.capture(), valueCaptor.capture());

        assertTrue(keyCaptor.getValue().startsWith("alarm-warning-service-"));

        String json = valueCaptor.getValue();
        assertTrue(json.contains("\"source\":\"alarm-warning-service\""));
        assertTrue(json.contains("\"eventType\":\"ALERT_CREATED\""));
        assertTrue(json.contains("\"alertEventCode\":\"ALT-test-001\""));
        assertTrue(json.contains("\"alertLevel\":\"RED\""));
        assertTrue(json.contains("\"priorityScore\":95"));
    }

    @Test
    void send_nullEvent_doesNotThrow() {
        assertDoesNotThrow(() -> alertEventProducer.send(null));
        verify(kafkaTemplate, never()).send(anyString(), anyString(), anyString());
    }

    @Test
    void send_serializationException_doesNotThrow() throws Exception {
        when(objectMapper.writeValueAsString(any())).thenThrow(new RuntimeException("Serialization error"));

        assertDoesNotThrow(() -> alertEventProducer.send(testEvent));
        verify(kafkaTemplate, never()).send(anyString(), anyString(), anyString());
    }

    @Test
    void send_kafkaSendFailure_doesNotThrow() {
        CompletableFuture<SendResult<String, String>> failedFuture = new CompletableFuture<>();
        failedFuture.completeExceptionally(new RuntimeException("Broker unavailable"));
        when(kafkaTemplate.send(eq("alert-event-topic"), anyString(), anyString()))
                .thenReturn(failedFuture);

        assertDoesNotThrow(() -> alertEventProducer.send(testEvent));
    }

    @Test
    void send_payloadContainsExpectedFields() throws Exception {
        CompletableFuture future = CompletableFuture.completedFuture(null);
        when(kafkaTemplate.send(eq("alert-event-topic"), anyString(), anyString()))
                .thenReturn(future);

        alertEventProducer.send(testEvent);

        ArgumentCaptor<String> valueCaptor = ArgumentCaptor.forClass(String.class);
        verify(kafkaTemplate).send(eq("alert-event-topic"), anyString(), valueCaptor.capture());

        String json = valueCaptor.getValue();
        assertTrue(json.contains("\"deviceId\":\"SENSOR-P-001\""));
        assertTrue(json.contains("\"deviceType\":\"PRESSURE\""));
        assertTrue(json.contains("\"areaId\":\"AREA-A01\""));
        assertTrue(json.contains("\"alertStatus\":\"OPEN\""));
        assertTrue(json.contains("\"rootCause\":\"PRESSURE_ABNORMAL\""));
        assertTrue(json.contains("\"mergedCount\":1"));
    }
}
