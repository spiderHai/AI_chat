import { ref, reactive, onMounted, watch } from "vue";
import { useRoute } from "vue-router";
import type {
  AdaptiveConfig,
  LoadingConfig,
  PaginationProps
} from "@pureadmin/table";
import { delay } from "@pureadmin/utils";

import { useWarehouseStore } from "@/store/modules/warehouse";
import { getShipConfirmPage } from "@/api/shipConfirm";

export type ShipConfirmSearch = {
  code: string;
  status: string;
  planDeliverDate: string;
  receiverName: string;
  receiverPhone: string;
  createdAt: string[];
  enterpriseName: string;
};

const compact = <T extends Record<string, any>>(source: T) => {
  const result: Record<string, any> = {};
  Object.entries(source || {}).forEach(([key, value]) => {
    if (
      value !== "" &&
      value !== undefined &&
      value !== null &&
      !(Array.isArray(value) && value.length === 0)
    ) {
      result[key] = value;
    }
  });
  return result as Partial<T>;
};

const createDefaultSearch = (): ShipConfirmSearch => ({
  code: "",
  status: "",
  planDeliverDate: "",
  receiverName: "",
  receiverPhone: "",
  createdAt: [],
  enterpriseName: ""
});

export function useShipConfirmList() {
  const warehouseStore = useWarehouseStore();
  const route = useRoute();

  const searchState = ref<ShipConfirmSearch>(createDefaultSearch());
  const dataList = ref<any[]>([]);
  const loading = ref(false);

  const pagination = reactive<PaginationProps>({
    pageSize: 20,
    currentPage: 1,
    pageSizes: [20, 40, 60],
    total: 0,
    align: "right",
    background: true,
    size: "default"
  });

  const loadingConfig: LoadingConfig = reactive({
    text: "正在加载...",
    viewBox: "-10, -10, 50, 50",
    spinner: `
      <path class="path" d="
        M 30 15 L 28 17
        M 25.61 25.61
        A 15 15, 0, 0, 1, 15 30
        A 15 15, 0, 1, 1, 27.99 7.5
        L 15 15
      " style="stroke-width: 4px; fill: rgba(0, 0, 0, 0)"/>`
  });

  const adaptiveConfig: AdaptiveConfig = { offsetBottom: 110 };

  async function fetchList() {
    if (!warehouseStore.selected?.id) {
      dataList.value = [];
      pagination.total = 0;
      return;
    }

    try {
      loading.value = true;
      const filters = compact(searchState.value);

      const planDeliverDate = filters.planDeliverDate as string | undefined;
      delete (filters as any).planDeliverDate;

      let crateStartTime: string | undefined;
      let crateEndTime: string | undefined;
      if (Array.isArray(filters.createdAt) && filters.createdAt.length === 2) {
        [crateStartTime, crateEndTime] = filters.createdAt as string[];
      }
      delete (filters as any).createdAt;

      const query = {
        pageNum: pagination.currentPage,
        pageSize: pagination.pageSize,
        warehouseId: warehouseStore.selected.id,
        planDeliverDate,
        crateStartTime,
        crateEndTime,
        ...(filters as Record<string, any>)
      };

      const resp: any = await getShipConfirmPage(query);
      const body = resp?.body ?? {};
      const list = body.pageData ?? body.list ?? [];

      dataList.value = Array.isArray(list) ? list : [];
      pagination.total =
        Number(body.totalSize ?? body.total ?? (list?.length ?? 0)) || 0;
    } finally {
      await delay(80);
      loading.value = false;
    }
  }

  async function handleSearch() {
    pagination.currentPage = 1;
    await fetchList();
  }

  async function handleReset() {
    searchState.value = createDefaultSearch();
    pagination.currentPage = 1;
    await fetchList();
  }

  async function onSizeChange(size: number) {
    pagination.pageSize = size;
    pagination.currentPage = 1;
    loadingConfig.text = "正在加载...";
    await fetchList();
  }

  async function onCurrentChange(page: number) {
    pagination.currentPage = page;
    loadingConfig.text = `正在加载第${page}页...`;
    await fetchList();
  }

  watch(
    () => warehouseStore.selected?.id,
    (newId, oldId) => {
      if (newId && newId !== oldId) {
        pagination.currentPage = 1;
        loadingConfig.text = "仓库切换，正在加载...";
        fetchList();
      }
    }
  );

  // 监听路由参数变化，支持从首页跳转过来自动触发查询
  watch(
    () => route.query,
    query => {
      const { status, fromHome } = query;
      // 检测到从首页跳转过来，并且带有状态参数
      if (fromHome === "true" && status) {
        // 设置搜索状态
        searchState.value.status = status as string;
        // 重置页码并触发查询
        pagination.currentPage = 1;
        loadingConfig.text = "正在加载待办事项...";
        fetchList();
      }
    },
    { immediate: true }
  );

  onMounted(fetchList);

  return {
    searchState,
    dataList,
    loading,
    pagination,
    loadingConfig,
    adaptiveConfig,
    fetchList,
    handleSearch,
    handleReset,
    onSizeChange,
    onCurrentChange
  };
}
