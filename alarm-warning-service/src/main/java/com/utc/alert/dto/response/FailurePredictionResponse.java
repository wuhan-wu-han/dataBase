package com.utc.alert.dto.response;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
public class FailurePredictionResponse {

    private Long id;
    private String deviceId;
    private String deviceType;
    private String areaId;
    private BigDecimal healthScore;
    private BigDecimal riskScore;
    private BigDecimal failureProbability;
    private Integer remainingLifeMonth;
    private String predictionLevel;
    private LocalDateTime predictionTime;
    private LocalDateTime createdAt;
}
