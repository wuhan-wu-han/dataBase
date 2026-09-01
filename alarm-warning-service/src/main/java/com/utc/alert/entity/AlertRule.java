package com.utc.alert.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
@TableName("alert_rule")
public class AlertRule {

    @TableId(type = IdType.AUTO)
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
