package com.utc.alert.dto.request;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

import java.math.BigDecimal;

@Data
public class UpdateAlertRuleRequest {

    @NotBlank(message = "ruleName不能为空")
    private String ruleName;

    @NotBlank(message = "deviceType不能为空")
    private String deviceType;

    @NotBlank(message = "metricKey不能为空")
    private String metricKey;

    private String areaId;

    private BigDecimal blueThreshold;

    private BigDecimal yellowThreshold;

    private BigDecimal orangeThreshold;

    private BigDecimal redThreshold;

    @NotBlank(message = "compareType不能为空")
    private String compareType;

    private Boolean enabled;

    private String description;
}
