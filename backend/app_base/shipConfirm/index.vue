<template>
  <div class="ship-confirm-page">
    <PlusSearch
      v-model="searchState"
      :columns="searchColumns"
      :show-number="3"
      label-width="120"
      search-text="搜索"
      label-position="right"
      @search="handleSearch"
      @reset="handleReset"
    />

    <pure-table
      border
      adaptive
      :adaptiveConfig="adaptiveConfig"
      row-key="id"
      alignWhole="center"
      showOverflowTooltip
      :loading="loading"
      :loading-config="loadingConfig"
      :data="dataList"
      :columns="tableColumns"
      :pagination="{
        ...pagination,
        layout: 'total, prev, pager, next, sizes, jumper'
      }"
      :header-cell-style="{
        background: 'var(--el-fill-color-light)',
        color: 'var(--el-text-color-primary)'
      }"
      @page-size-change="onSizeChange"
      @page-current-change="onCurrentChange"
    >
      <template #status="{ row }">
        <el-tag :type="statusTagType(row)" effect="plain">
          {{ row.statusDesc || "-" }}
        </el-tag>
      </template>

      <template #action="{ row }">
        <el-space wrap size="small">
          <el-link type="primary" @click="handleGoDetail(row)">
            {{ isPending(row) ? "去发货" : "查看详情" }}
          </el-link>
          <el-divider direction="vertical" />
          <el-link type="primary" @click="handleDownload(row)">
            下载发货单
          </el-link>
        </el-space>
      </template>
    </pure-table>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from "element-plus";
import { PlusSearch } from "plus-pro-components";
import "plus-pro-components/es/components/search/style/css";

import { openOverlay } from "@/components/PageOverlay/usePageOverlay";
import { searchColumns, tableColumns, STATUS_TAG_MAP } from "./columns";
import { useShipConfirmList } from "./useShipConfirmList";
import { downloadShipConfirmOrder } from "@/api/shipConfirm";

defineOptions({ name: "ShipConfirm" });

const {
  searchState,
  handleSearch,
  handleReset,
  loading,
  dataList,
  pagination,
  loadingConfig,
  adaptiveConfig,
  onSizeChange,
  onCurrentChange,
  fetchList
} = useShipConfirmList();

const statusTagType = (row: Record<string, any>) => {
  const code = row?.status || mapDescToStatus(row?.statusDesc);
  return STATUS_TAG_MAP[code || ""] || "info";
};

const mapDescToStatus = (desc?: string) => {
  if (!desc) return "";
  if (desc.includes("待确认")) return "PENDING";
  if (desc.includes("已确认")) return "CONFIRMED";
  if (desc.includes("撤销")) return "CANCELED";
  return "";
};

const isPending = (row: Record<string, any>) =>
  row?.status === "PENDING" || mapDescToStatus(row?.statusDesc) === "PENDING";

function handleGoDetail(row: Record<string, any>) {
  if (!row?.id) {
    ElMessage.warning("缺少单据ID，无法查看详情");
    return;
  }

  const pending = isPending(row);
  openOverlay({
    key: `ShipConfirmDetail-${row.id}`,
    title: pending ? "确认发货" : "发货确认详情",
    loader: () => import("./detail/index.vue"),
    props: {
      id: row.id,
      base: row,
      mode: pending ? "confirm" : "view",
      onSuccess: fetchList
    },
    keepAlive: true,
    nopadding: false,
    zIndex: 5000
  });
}

async function handleDownload(row: Record<string, any>) {
  if (!row?.id) {
    ElMessage.warning("缺少单据ID，无法下载");
    return;
  }

  try {
    await downloadShipConfirmOrder(row.id);
  } catch (error: any) {
    ElMessage.error(error?.message || "发货单下载失败");
  }
}
</script>

<style scoped>
.ship-confirm-page {
  padding: 16px 20px 20px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}
</style>
