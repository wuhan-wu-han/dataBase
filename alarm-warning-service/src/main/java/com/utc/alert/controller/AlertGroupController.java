package com.utc.alert.controller;

import com.utc.alert.common.result.Result;
import com.utc.alert.dto.request.AlertGroupQueryRequest;
import com.utc.alert.dto.response.AlertGroupResponse;
import com.utc.alert.dto.response.PageResponse;
import com.utc.alert.service.AlertGroupService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/alert-groups")
@RequiredArgsConstructor
public class AlertGroupController {

    private final AlertGroupService alertGroupService;

    @GetMapping
    public Result<PageResponse<AlertGroupResponse>> getGroups(AlertGroupQueryRequest request) {
        return Result.success(alertGroupService.getGroups(request));
    }

    @GetMapping("/{id}")
    public Result<AlertGroupResponse> getGroupById(@PathVariable Long id) {
        return Result.success(alertGroupService.getGroupById(id));
    }
}
