package com.utc.alert.service;

import com.utc.alert.dto.request.AlertGroupQueryRequest;
import com.utc.alert.dto.response.AlertGroupResponse;
import com.utc.alert.dto.response.PageResponse;

public interface AlertGroupService {

    PageResponse<AlertGroupResponse> getGroups(AlertGroupQueryRequest request);

    AlertGroupResponse getGroupById(Long id);
}
