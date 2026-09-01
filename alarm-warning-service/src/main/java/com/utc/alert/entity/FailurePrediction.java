package com.utc.alert.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
@TableName("failure_prediction")
public class FailurePrediction {

    @TableId(type = IdType.AUTO)
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
