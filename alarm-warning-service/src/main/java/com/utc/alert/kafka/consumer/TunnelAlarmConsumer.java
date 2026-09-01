package com.utc.alert.kafka.consumer;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.utc.alert.dto.kafka.KafkaMessage;
import com.utc.alert.service.AlertEngineService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

@Slf4j
@Component
@RequiredArgsConstructor
public class TunnelAlarmConsumer {

    private final ObjectMapper objectMapper;
    private final AlertEngineService alertEngineService;

    @KafkaListener(
            topics = "${alert.kafka.topics.tunnel-alarm}",
            groupId = "${spring.kafka.consumer.group-id}"
    )
    public void consume(String message) {
        try {
            KafkaMessage kafkaMessage = objectMapper.readValue(message, KafkaMessage.class);

            if (kafkaMessage.getEventId() == null || kafkaMessage.getSource() == null
                    || kafkaMessage.getTimestamp() == null || kafkaMessage.getEventType() == null) {
                log.warn("Invalid alarm message, missing required fields: {}", message);
                return;
            }

            log.info("Received alarm event: eventId={}, deviceId={}, eventType={}",
                    kafkaMessage.getEventId(), kafkaMessage.getDeviceId(), kafkaMessage.getEventType());

            alertEngineService.processMessage(kafkaMessage);
        } catch (Exception e) {
            log.error("Kafka message consume failed, topic=tunnel-alarm-topic, message={}", message, e);
        }
    }
}
