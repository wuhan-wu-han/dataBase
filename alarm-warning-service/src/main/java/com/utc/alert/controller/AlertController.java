package com.utc.alert.controller;

import com.utc.alert.common.result.Result;
import com.utc.alert.dto.request.AlertQueryRequest;
import com.utc.alert.dto.request.UpdateAlertStatusRequest;
import com.utc.alert.dto.response.AlertResponse;
import com.utc.alert.dto.response.PageResponse;
import com.utc.alert.service.AlertService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/alerts")
@RequiredArgsConstructor
public class AlertController {

    private final AlertService alertService;

    @GetMapping
    public Result<PageResponse<AlertResponse>> getAlerts(AlertQueryRequest request) {
        return Result.success(alertService.getAlerts(request));
    }

    @GetMapping("/{id}")
    public Result<AlertResponse> getAlertById(@PathVariable Long id) {
        return Result.success(alertService.getAlertById(id));
    }

    @PatchMapping("/{id}/status")
    public Result<AlertResponse> updateAlertStatus(@PathVariable Long id,
                                                   @Valid @RequestBody UpdateAlertStatusRequest request) {
        return Result.success(alertService.updateAlertStatus(id, request));
    }
}
