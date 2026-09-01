package com.utc.alert.dto.response;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
public class AlertResponse {

    private Long id;
    private String alertEventCode;
    private String sourceEventId;
    private String source;
    private String deviceId;
    private String deviceType;
    private String zone;
    private String areaId;
    private String alertLevel;
    private String alertStatus;
    private String metricKey;
    private BigDecimal metricValue;
    private BigDecimal thresholdValue;
    private String rootCause;
    private String rootCauseDesc;
    private Integer priorityScore;
    private Long alertGroupId;
    private Integer mergedCount;
    private Long eventTimestamp;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
