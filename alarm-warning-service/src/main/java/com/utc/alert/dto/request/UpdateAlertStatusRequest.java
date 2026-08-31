package com.utc.alert.dto.request;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class UpdateAlertStatusRequest {

    @NotBlank(message = "status不能为空")
    private String status;
}
