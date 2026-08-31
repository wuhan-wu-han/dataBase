package com.utc.alert.dto.kafka;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Data;

import java.util.Map;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class KafkaMessage {

    private String eventId;

    private String source;

    private String deviceId;

    private String deviceType;

    private LocationInfo location;

    private Long timestamp;

    private String eventType;

    private String alarmCode;

    private String alarmLevel;

    private Map<String, Object> metrics;

    private Double healthScore;

    private Map<String, Object> payload;
}
