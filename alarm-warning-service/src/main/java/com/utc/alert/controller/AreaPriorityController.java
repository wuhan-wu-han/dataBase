package com.utc.alert.controller;

import com.utc.alert.common.result.Result;
import com.utc.alert.dto.response.AreaPriorityResponse;
import com.utc.alert.service.AreaPriorityService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/area-priority")
@RequiredArgsConstructor
public class AreaPriorityController {

    private final AreaPriorityService areaPriorityService;

    @GetMapping
    public Result<List<AreaPriorityResponse>> getAllAreaPriorities() {
        return Result.success(areaPriorityService.getAllAreaPriorities());
    }
}
