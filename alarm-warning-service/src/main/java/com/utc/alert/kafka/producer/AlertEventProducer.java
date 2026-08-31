package com.utc.alert.kafka.producer;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.utc.alert.dto.kafka.KafkaMessage;
import com.utc.alert.entity.AlertEvent;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

@Slf4j
@Component
@RequiredArgsConstructor
public class AlertEventProducer {

    private final KafkaTemplate<String, String> kafkaTemplate;
    private final ObjectMapper objectMapper;

    @Value("${alert.kafka.topics.alert-event}")
    private String topic;

    public void send(AlertEvent alertEvent) {
        if (alertEvent == null) {
            log.warn("Cannot send null alert event, skipping");
            return;
        }

        String eventId = "alarm-warning-service-" + UUID.randomUUID();

        try {
            KafkaMessage message = new KafkaMessage();
            message.setEventId(eventId);
            message.setSource("alarm-warning-service");
            message.setTimestamp(System.currentTimeMillis());
            message.setEventType("ALERT_CREATED");
            message.setDeviceId(alertEvent.getDeviceId());
            message.setDeviceType(alertEvent.getDeviceType());

            Map<String, Object> payload = new HashMap<>();
            payload.put("alertEventCode", alertEvent.getAlertEventCode());
            payload.put("deviceId", alertEvent.getDeviceId());
            payload.put("deviceType", alertEvent.getDeviceType());
            payload.put("areaId", alertEvent.getAreaId());
            payload.put("alertLevel", alertEvent.getAlertLevel());
            payload.put("alertStatus", alertEvent.getAlertStatus());
            payload.put("rootCause", alertEvent.getRootCause());
            payload.put("priorityScore", alertEvent.getPriorityScore());
            payload.put("mergedCount", alertEvent.getMergedCount());
            message.setPayload(payload);

            String jsonMessage = objectMapper.writeValueAsString(message);

            kafkaTemplate.send(topic, eventId, jsonMessage).whenComplete((result, ex) -> {
                if (ex != null) {
                    log.error("Failed to publish alert event: topic={}, eventId={}",
                            topic, eventId, ex);
                } else {
                    log.info("Alert event published successfully: eventId={}, topic={}",
                            eventId, topic);
                }
            });
        } catch (Exception e) {
            log.error("Failed to send alert event to Kafka: topic={}, eventId={}",
                    topic, eventId, e);
        }
    }
}
