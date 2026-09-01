package com.utc.alert.dto.response;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
public class AlertRuleResponse {

    private Long id;
    private String ruleCode;
    private String ruleName;
    private String deviceType;
    private String metricKey;
    private String areaId;
    private BigDecimal blueThreshold;
    private BigDecimal yellowThreshold;
    private BigDecimal orangeThreshold;
    private BigDecimal redThreshold;
    private String compareType;
    private Boolean enabled;
    private String description;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
