<template>
  <div class="ship-confirm-detail" v-loading="loading">
    <DocumentInfo :items="infoItems">
      <template #extra>
        <el-button v-if="docId" @click="handleDownload">下载发货单</el-button>
      </template>
    </DocumentInfo>

    <section class="detail-section">
      <DocTitle text="单据详情" tag="h3" />

      <pure-table
        v-if="pagedGoods.length"
        :row-key="rowKey"
        :data="pagedGoods"
        :columns="columns"
        showOverflowTooltip
        alignWhole="center"
        :header-cell-style="{
          background: 'var(--el-fill-color-light)',
          color: 'var(--el-text-color-primary)'
        }"
      >
        <template #skuImage="{ row }">
          <el-image
            v-if="row.skuDefaultImgUrl"
            :src="row.skuDefaultImgUrl"
            fit="contain"
            class="thumb"
            :preview-src-list="[row.skuDefaultImgUrl]"
            :z-index="3000"
            preview-teleported
          />
          <span v-else>-</span>
        </template>

        <template #deliverQty="{ row }">
          <div v-if="isPendingStatus" class="ship-input">
            <el-input-number
              v-model.number="row.editableDeliverQty"
              :min="0"
              :max="resolveMaxQty(row)"
              :precision="0"
              controls-position="right"
              size="small"
            />
          </div>
          <span v-else>{{ displayReadonlyQty(row) }}</span>
        </template>
      </pure-table>

      <el-empty
        v-else
        description="暂无单据明细"
        :image-size="120"
        class="empty-block"
      />

      <div class="pager" v-if="allGoods.length > pagination.pageSize">
        <el-pagination
          background
          layout="prev, pager, next, sizes, total"
          :total="allGoods.length"
          :current-page="pagination.current"
          :page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50]"
          @update:current-page="handlePageChange"
          @update:page-size="handleSizeChange"
        />
      </div>
    </section>

    <div v-if="isPendingStatus" class="footer">
      <!-- 左侧统计 -->
      <div class="footer-summary">
        下单：{{ orderSummaryText }} / 发货：{{ deliverSummaryText }}
      </div>

      <!-- 右侧按钮 -->
      <el-space>
        <el-button
          type="primary"
          :loading="submitLoading"
          @click="handleConfirm"
        >
          确认发货
        </el-button>
      </el-space>
    </div>

    <CheckDialog
      v-model:visible="showCheckDialog"
      :rows="mismatchGoods"
      @confirm="handleCheckConfirm"
    />

    <ConfirmDialog
      v-model:visible="showConfirmDialog"
      @confirm="handleConfirmSubmit"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, watch } from "vue";
import { ElMessage } from "element-plus";

import DocumentInfo from "@/components/DocumentInfo/index.vue";
import DocTitle from "@/components/DocTitle/index.vue";
import { useOverlayClose } from "@/components/PageOverlay/store";
import CheckDialog from "./CheckDialog.vue";
import ConfirmDialog from "./ConfirmDialog.vue";
import {
  getShipConfirmDetail,
  confirmShipConfirmOrder,
  downloadShipConfirmOrder
} from "@/api/shipConfirm";

const props = defineProps<{
  id?: string | number;
  base?: Record<string, any>;
  mode?: "confirm" | "view";
  onSuccess?: () => void;
}>();

const overlayClose = useOverlayClose();
const docId = computed(() => (props.id != null ? String(props.id) : ""));

const loading = ref(false);
const submitLoading = ref(false);
const showCheckDialog = ref(false);
const showConfirmDialog = ref(false);
const detail = ref<Record<string, any>>({});
const allGoods = ref<Record<string, any>[]>([]);

const pagination = ref({ current: 1, pageSize: 10 });
const pagedGoods = computed(() => {
  const start = (pagination.value.current - 1) * pagination.value.pageSize;
  return allGoods.value.slice(start, start + pagination.value.pageSize);
});

const isPendingStatus = computed(() => {
  if (props.mode === "confirm") return true;
  const status = detail.value?.status;
  const desc = detail.value?.statusDesc;
  return status === "PENDING" || desc === "待确认";
});

const infoItems = computed(() => {
  const d = detail.value || {};
  const receiverBase = props.base || {};
  const receiverInfo =
    [
      receiverBase.receiverName || d.receiverName,
      receiverBase.receiverPhone || d.receiverPhone
    ]
      .filter(Boolean)
      .join(" / ") || "-";
  const address =
    receiverBase.receiverAddress ||
    d.receiverAddress ||
    receiverBase.receiverDetailAddress ||
    "-";

  return [
    { label: "确认单编号", value: d.code || "-" },
    {
      label: "来源编号",
      value: d.mallOrderId || receiverBase.mallOrderId || "-"
    },
    { label: "仓库名称", value: d.warehouseName || "-" },
    { label: "计划发货日", value: d.planDeliverDate || "-" },
    { label: "单据状态", value: d.statusDesc || d.status || "-" },
    { label: "下单数量", value: d.orderQtyDesc || "-" },
    { label: "发货数量", value: d.deliverQtyDesc || "-" },
    { label: "创建时间", value: d.createTime || "-" },
    { label: "确认完成时间", value: d.confirmTime || "-" },
    { label: "收件人信息", value: receiverInfo },
    { label: "收货地址", value: address }
  ];
});

const rowKey = (row: Record<string, any>) =>
  row.id ?? row.deliveryConfirmId ?? row.skuId ?? row.skuCode;

const columns = [
  { type: "index", label: "序号", width: 60 },
  { label: "商品图片", prop: "skuDefaultImgUrl", slot: "skuImage", width: 120 },
  { label: "商品名称", prop: "skuName", minWidth: 220, align: "left" },
  { label: "SKU编码", prop: "skuCode", minWidth: 160 },
  { label: "规格", prop: "skuSpec", minWidth: 120 },
  { label: "下单数量", prop: "orderQty", minWidth: 120 },
  { label: "备货数量", prop: "availableQty", minWidth: 120 },
  { label: "发货数量", prop: "deliverQty", slot: "deliverQty", minWidth: 140 }
];

const displayReadonlyQty = (row: Record<string, any>) => {
  const candidates = [
    row.deliverQty,
    row.editableDeliverQty,
    row.planDeliverQty,
    row.orderQty
  ];
  for (const val of candidates) {
    if (val === null || val === undefined) continue;
    const num = Number(val);
    if (Number.isNaN(num)) continue;
    return num;
  }
  return "-";
};

const toNumber = (value: unknown) => {
  const num = Number(value);
  return Number.isNaN(num) ? 0 : num;
};

const resolveMaxQty = (row: Record<string, any>) => {
  const availableQty = toNumber(row.availableQty);
  const orderQty = toNumber(row.orderQty);
  if (availableQty > 0) return availableQty;
  if (orderQty > 0) return orderQty;
  return Number.MAX_SAFE_INTEGER;
};

const normalizeGoods = (list: Record<string, any>[]) =>
  (list || []).map(item => ({
    ...item,
    editableDeliverQty: toNumber(item?.deliverQty) || toNumber(item.orderQty)
  }));

const mismatchGoods = computed(() =>
  allGoods.value
    .filter(item => {
      const deliverQty = toNumber(item.editableDeliverQty);
      return (
        deliverQty !== toNumber(item.availableQty) ||
        deliverQty !== toNumber(item.orderQty)
      );
    })
    .map(item => ({
      ...item,
      orderQty: toNumber(item.orderQty),
      availableQty: toNumber(item.availableQty),
      deliverQty: toNumber(item.editableDeliverQty)
    }))
);

async function fetchDetail() {
  if (!docId.value) {
    detail.value = props.base || {};
    allGoods.value = [];
    return;
  }
  try {
    loading.value = true;
    const res: any = await getShipConfirmDetail(docId.value);
    const body = res?.body ?? {};
    detail.value = { ...(props.base || {}), ...body };
    const list = Array.isArray(body.detailList) ? body.detailList : [];
    allGoods.value = normalizeGoods(list);
    pagination.value.current = 1;
  } catch (error: any) {
    ElMessage.error(error?.message || "获取发货确认单详情失败");
  } finally {
    loading.value = false;
  }
}

onMounted(fetchDetail);
watch(
  () => docId.value,
  id => {
    if (id) fetchDetail();
  }
);

function handlePageChange(page: number) {
  pagination.value.current = page;
}

function handleSizeChange(size: number) {
  pagination.value.pageSize = size;
  pagination.value.current = 1;
}

function handleClose() {
  overlayClose?.();
}

async function handleConfirm() {
  if (!docId.value) {
    ElMessage.warning("缺少单据ID，无法确认发货");
    return;
  }
  if (!allGoods.value.length) {
    ElMessage.warning("暂无单据明细，无法确认发货");
    return;
  }

  const payloadDetails = allGoods.value.map(item => {
    // const identifier =
    //   item.id ?? item.detailId ?? item.deliveryConfirmId ?? item.skuId;
    return {
      // detailId: identifier,
      deliverQty: Number(item.editableDeliverQty ?? 0),
      skuId: item.skuId
    };
  });

  const invalid = payloadDetails.find((item, index) => {
    // if (!item.detailId) return true;
    if (item.deliverQty < 0) return true;
    const origin = allGoods.value[index];
    const max = resolveMaxQty(origin);
    return item.deliverQty > max;
  });

  if (invalid) {
    ElMessage.warning("发货数量不合法，请检查后再试");
    return;
  }

  // 显示自定义确认对话框
  if (mismatchGoods.value.length) {
    showCheckDialog.value = true;
    return;
  }

  showConfirmDialog.value = true;
}

function handleCheckConfirm() {
  showConfirmDialog.value = true;
}

async function handleConfirmSubmit() {
  try {
    submitLoading.value = true;

    const payloadDetails = allGoods.value.map(item => ({
      deliverQty: Number(item.editableDeliverQty ?? 0),
      skuId: item.skuId
    }));

    await confirmShipConfirmOrder({
      id: docId.value,
      detailList: payloadDetails
    });
    ElMessage.success("发货确认成功");
    props.onSuccess?.();
    handleClose();
  } catch (error: any) {
    ElMessage.error(error?.message || "发货确认失败");
  } finally {
    submitLoading.value = false;
  }
}

async function handleDownload() {
  if (!docId.value) {
    ElMessage.warning("缺少单据ID，无法下载");
    return;
  }
  try {
    await downloadShipConfirmOrder(docId.value);
  } catch (error: any) {
    ElMessage.error(error?.message || "下载失败");
  }
}
// 下单合计：种数 = 行数，总件数 = sum(orderQty)
const orderSummaryText = computed(() => {
  const list = allGoods.value || [];
  if (!list.length) return "-";
  const categoryCount = list.length;
  const totalQty = list.reduce(
    (sum, item) => sum + Number(item.orderQty || 0),
    0
  );
  return `${categoryCount}种${totalQty}件`;
});

// 发货合计：
// 总件数 = sum(当前行可编辑的 editableDeliverQty)
// 种数 = 发货数量 > 0 的行数（为 0 的行不算一种）
const deliverSummaryText = computed(() => {
  const list = allGoods.value || [];
  if (!list.length) return "-";

  let categoryCount = 0;
  let totalQty = 0;

  for (const item of list) {
    const qty = Number(
      item.editableDeliverQty ?? item.deliverQty ?? item.planDeliverQty ?? 0
    );
    if (qty > 0) categoryCount += 1;
    totalQty += qty;
  }

  return `${categoryCount}种${totalQty}件`;
});
</script>

<style scoped>
.ship-confirm-detail {
  padding: 0px 20px 0px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-section {
  background: #fff;
  padding: 16px 20px 20px;
}

.thumb {
  width: 56px;
  height: 56px;
  border-radius: 4px;
  border: 1px solid var(--el-border-color);
}

.ship-input {
  display: flex;
  justify-content: center;
}

.empty-block {
  background: #fff;
  padding: 36px 0;
  border: 1px dashed var(--el-border-color);
}

.pager {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}

.footer {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding-top: 8px;
  padding-right: 20px;
}

.footer-summary {
  font-size: 16px;
  color: #606266;
  padding-right: 20px;
  font-weight: 500;
}
</style>
