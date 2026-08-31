package com.utc.alert.controller;

import com.utc.alert.common.result.Result;
import com.utc.alert.dto.request.AlertRuleQueryRequest;
import com.utc.alert.dto.request.CreateAlertRuleRequest;
import com.utc.alert.dto.request.UpdateAlertRuleRequest;
import com.utc.alert.dto.response.AlertRuleResponse;
import com.utc.alert.dto.response.PageResponse;
import com.utc.alert.service.AlertRuleService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/alert-rules")
@RequiredArgsConstructor
public class AlertRuleController {

    private final AlertRuleService alertRuleService;

    @GetMapping
    public Result<PageResponse<AlertRuleResponse>> getRules(AlertRuleQueryRequest request) {
        return Result.success(alertRuleService.getRules(request));
    }

    @PostMapping
    public Result<AlertRuleResponse> createRule(@Valid @RequestBody CreateAlertRuleRequest request) {
        return Result.success(alertRuleService.createRule(request));
    }

    @PutMapping("/{id}")
    public Result<AlertRuleResponse> updateRule(@PathVariable Long id,
                                                @Valid @RequestBody UpdateAlertRuleRequest request) {
        return Result.success(alertRuleService.updateRule(id, request));
    }

    @DeleteMapping("/{id}")
    public Result<Void> deleteRule(@PathVariable Long id) {
        alertRuleService.deleteRule(id);
        return Result.success();
    }
}
