package com.utc.alert.dto.response;

import com.baomidou.mybatisplus.core.metadata.IPage;
import lombok.Data;

import java.util.List;

@Data
public class PageResponse<T> {

    private List<T> records;
    private long total;
    private int page;
    private int size;
    private long pages;

    public static <T> PageResponse<T> of(IPage<?> pageResult, List<T> records) {
        PageResponse<T> response = new PageResponse<>();
        response.setRecords(records);
        response.setTotal(pageResult.getTotal());
        response.setPage((int) pageResult.getCurrent());
        response.setSize((int) pageResult.getSize());
        response.setPages(pageResult.getPages());
        return response;
    }
}
