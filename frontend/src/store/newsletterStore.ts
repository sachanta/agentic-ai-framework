/**
 * Zustand store for Newsletter platform state
 *
 * Manages client-side state for:
 * - Active workflow tracking
 * - Checkpoint data
 * - Selected articles
 * - Form drafts
 * - UI preferences
 */
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type {
  Article,
  WorkflowStepStatus,
  Checkpoint,
  SSECheckpointEvent,
} from '@/types/newsletter';

// ============================================================================
// STATE TYPES
// ============================================================================

interface WorkflowUIState {
  activeWorkflowId: string | null;
  workflowStatus: WorkflowStepStatus | null;
  checkpointData: SSECheckpointEvent | Checkpoint | null;
}

interface ArticleSelectionState {
  selectedArticles: Article[];
  articleSortOrder: string[];
}

interface FormDraftState {
  researchTopics: string[];
  selectedTone: string;
  customPrompt: string;
  maxArticles: number;
}

interface UIPreferencesState {
  showPreview: boolean;
  previewFormat: 'html' | 'text' | 'markdown';
  listViewMode: 'grid' | 'list';
  sidebarExpanded: boolean;
}

interface NewsletterState extends
  WorkflowUIState,
  ArticleSelectionState,
  FormDraftState,
  UIPreferencesState {
  // Workflow actions
  setActiveWorkflow: (id: string | null) => void;
  setWorkflowStatus: (status: WorkflowStepStatus | null) => void;
  setCheckpointData: (data: SSECheckpointEvent | Checkpoint | null) => void;
  clearWorkflowState: () => void;

  // Article selection actions
  selectArticle: (article: Article) => void;
  deselectArticle: (url: string) => void;
  toggleArticle: (article: Article) => void;
  clearSelectedArticles: () => void;
  reorderArticles: (fromIndex: number, toIndex: number) => void;
  setSelectedArticles: (articles: Article[]) => void;

  // Form draft actions
  setResearchTopics: (topics: string[]) => void;
  addResearchTopic: (topic: string) => void;
  removeResearchTopic: (topic: string) => void;
  setSelectedTone: (tone: string) => void;
  setCustomPrompt: (prompt: string) => void;
  setMaxArticles: (count: number) => void;
  clearFormDraft: () => void;

  // UI preference actions
  togglePreview: () => void;
  setPreviewFormat: (format: 'html' | 'text' | 'markdown') => void;
  setListViewMode: (mode: 'grid' | 'list') => void;
  toggleSidebar: () => void;

  // Reset all state
  resetAll: () => void;
}

// ============================================================================
// INITIAL STATE
// ============================================================================

const initialWorkflowState: WorkflowUIState = {
  activeWorkflowId: null,
  workflowStatus: null,
  checkpointData: null,
};

const initialArticleState: ArticleSelectionState = {
  selectedArticles: [],
  articleSortOrder: [],
};

const initialFormState: FormDraftState = {
  researchTopics: [],
  selectedTone: 'professional',
  customPrompt: '',
  maxArticles: 10,
};

const initialUIPreferences: UIPreferencesState = {
  showPreview: true,
  previewFormat: 'html',
  listViewMode: 'grid',
  sidebarExpanded: true,
};

// ============================================================================
// STORE
// ============================================================================

export const useNewsletterStore = create<NewsletterState>()(
  persist(
    (set, get) => ({
      // Initial state
      ...initialWorkflowState,
      ...initialArticleState,
      ...initialFormState,
      ...initialUIPreferences,

      // ========================================================================
      // WORKFLOW ACTIONS
      // ========================================================================

      setActiveWorkflow: (id) => set({ activeWorkflowId: id }),

      setWorkflowStatus: (status) => set({ workflowStatus: status }),

      setCheckpointData: (data) => set({ checkpointData: data }),

      clearWorkflowState: () => set(initialWorkflowState),

      // ========================================================================
      // ARTICLE SELECTION ACTIONS
      // ========================================================================

      selectArticle: (article) => {
        const { selectedArticles, articleSortOrder } = get();
        if (!selectedArticles.find((a) => a.url === article.url)) {
          set({
            selectedArticles: [...selectedArticles, article],
            articleSortOrder: [...articleSortOrder, article.url],
          });
        }
      },

      deselectArticle: (url) => {
        const { selectedArticles, articleSortOrder } = get();
        set({
          selectedArticles: selectedArticles.filter((a) => a.url !== url),
          articleSortOrder: articleSortOrder.filter((u) => u !== url),
        });
      },

      toggleArticle: (article) => {
        const { selectedArticles } = get();
        const isSelected = selectedArticles.some((a) => a.url === article.url);
        if (isSelected) {
          get().deselectArticle(article.url);
        } else {
          get().selectArticle(article);
        }
      },

      clearSelectedArticles: () => set(initialArticleState),

      reorderArticles: (fromIndex, toIndex) => {
        const { articleSortOrder, selectedArticles } = get();
        const newOrder = [...articleSortOrder];
        const [moved] = newOrder.splice(fromIndex, 1);
        newOrder.splice(toIndex, 0, moved);

        // Reorder selectedArticles to match
        const orderedArticles = newOrder
          .map((url) => selectedArticles.find((a) => a.url === url))
          .filter((a): a is Article => a !== undefined);

        set({
          articleSortOrder: newOrder,
          selectedArticles: orderedArticles,
        });
      },

      setSelectedArticles: (articles) => set({
        selectedArticles: articles,
        articleSortOrder: articles.map((a) => a.url),
      }),

      // ========================================================================
      // FORM DRAFT ACTIONS
      // ========================================================================

      setResearchTopics: (topics) => set({ researchTopics: topics }),

      addResearchTopic: (topic) => {
        const { researchTopics } = get();
        const trimmed = topic.trim();
        if (trimmed && !researchTopics.includes(trimmed)) {
          set({ researchTopics: [...researchTopics, trimmed] });
        }
      },

      removeResearchTopic: (topic) => {
        const { researchTopics } = get();
        set({ researchTopics: researchTopics.filter((t) => t !== topic) });
      },

      setSelectedTone: (tone) => set({ selectedTone: tone }),

      setCustomPrompt: (prompt) => set({ customPrompt: prompt }),

      setMaxArticles: (count) => set({ maxArticles: Math.max(1, Math.min(50, count)) }),

      clearFormDraft: () => set(initialFormState),

      // ========================================================================
      // UI PREFERENCE ACTIONS
      // ========================================================================

      togglePreview: () => set((state) => ({ showPreview: !state.showPreview })),

      setPreviewFormat: (format) => set({ previewFormat: format }),

      setListViewMode: (mode) => set({ listViewMode: mode }),

      toggleSidebar: () => set((state) => ({ sidebarExpanded: !state.sidebarExpanded })),

      // ========================================================================
      // RESET
      // ========================================================================

      resetAll: () => set({
        ...initialWorkflowState,
        ...initialArticleState,
        ...initialFormState,
        ...initialUIPreferences,
      }),
    }),
    {
      name: 'newsletter-storage',
      storage: createJSONStorage(() => localStorage),
      // Only persist UI preferences and form drafts, not workflow state
      partialize: (state) => ({
        researchTopics: state.researchTopics,
        selectedTone: state.selectedTone,
        maxArticles: state.maxArticles,
        showPreview: state.showPreview,
        previewFormat: state.previewFormat,
        listViewMode: state.listViewMode,
        sidebarExpanded: state.sidebarExpanded,
      }),
    }
  )
);

// ============================================================================
// SELECTORS (for performance optimization)
// ============================================================================

// Workflow selectors
export const selectActiveWorkflow = (state: NewsletterState) => state.activeWorkflowId;
export const selectWorkflowStatus = (state: NewsletterState) => state.workflowStatus;
export const selectCheckpointData = (state: NewsletterState) => state.checkpointData;
export const selectIsWorkflowActive = (state: NewsletterState) =>
  state.activeWorkflowId !== null && state.workflowStatus === 'running';
export const selectIsAwaitingApproval = (state: NewsletterState) =>
  state.workflowStatus === 'awaiting_approval';

// Article selectors
export const selectSelectedArticles = (state: NewsletterState) => state.selectedArticles;
export const selectSelectedArticleCount = (state: NewsletterState) => state.selectedArticles.length;
export const selectIsArticleSelected = (url: string) => (state: NewsletterState) =>
  state.selectedArticles.some((a) => a.url === url);
export const selectHasSelectedArticles = (state: NewsletterState) =>
  state.selectedArticles.length > 0;

// Form selectors
export const selectResearchTopics = (state: NewsletterState) => state.researchTopics;
export const selectSelectedTone = (state: NewsletterState) => state.selectedTone;
export const selectCustomPrompt = (state: NewsletterState) => state.customPrompt;
export const selectMaxArticles = (state: NewsletterState) => state.maxArticles;
export const selectHasTopics = (state: NewsletterState) => state.researchTopics.length > 0;

// UI selectors
export const selectShowPreview = (state: NewsletterState) => state.showPreview;
export const selectPreviewFormat = (state: NewsletterState) => state.previewFormat;
export const selectListViewMode = (state: NewsletterState) => state.listViewMode;
export const selectSidebarExpanded = (state: NewsletterState) => state.sidebarExpanded;

// ============================================================================
// HOOKS FOR COMMON PATTERNS
// ============================================================================

/**
 * Hook to get article selection state and actions
 */
export function useArticleSelection() {
  const selectedArticles = useNewsletterStore(selectSelectedArticles);
  const selectedCount = useNewsletterStore(selectSelectedArticleCount);
  const hasSelected = useNewsletterStore(selectHasSelectedArticles);
  const selectArticle = useNewsletterStore((s) => s.selectArticle);
  const deselectArticle = useNewsletterStore((s) => s.deselectArticle);
  const toggleArticle = useNewsletterStore((s) => s.toggleArticle);
  const clearSelectedArticles = useNewsletterStore((s) => s.clearSelectedArticles);
  const reorderArticles = useNewsletterStore((s) => s.reorderArticles);
  const setSelectedArticles = useNewsletterStore((s) => s.setSelectedArticles);

  return {
    selectedArticles,
    selectedCount,
    hasSelected,
    selectArticle,
    deselectArticle,
    toggleArticle,
    clearSelectedArticles,
    reorderArticles,
    setSelectedArticles,
    isSelected: (url: string) => selectedArticles.some((a) => a.url === url),
  };
}

/**
 * Hook to get workflow state and actions
 */
export function useWorkflowState() {
  const activeWorkflowId = useNewsletterStore(selectActiveWorkflow);
  const status = useNewsletterStore(selectWorkflowStatus);
  const checkpointData = useNewsletterStore(selectCheckpointData);
  const isActive = useNewsletterStore(selectIsWorkflowActive);
  const isAwaitingApproval = useNewsletterStore(selectIsAwaitingApproval);
  const setActiveWorkflow = useNewsletterStore((s) => s.setActiveWorkflow);
  const setWorkflowStatus = useNewsletterStore((s) => s.setWorkflowStatus);
  const setCheckpointData = useNewsletterStore((s) => s.setCheckpointData);
  const clearWorkflowState = useNewsletterStore((s) => s.clearWorkflowState);

  return {
    activeWorkflowId,
    status,
    checkpointData,
    isActive,
    isAwaitingApproval,
    setActiveWorkflow,
    setWorkflowStatus,
    setCheckpointData,
    clearWorkflowState,
  };
}

/**
 * Hook to get form draft state and actions
 */
export function useFormDraft() {
  const topics = useNewsletterStore(selectResearchTopics);
  const tone = useNewsletterStore(selectSelectedTone);
  const customPrompt = useNewsletterStore(selectCustomPrompt);
  const maxArticles = useNewsletterStore(selectMaxArticles);
  const hasTopics = useNewsletterStore(selectHasTopics);
  const setResearchTopics = useNewsletterStore((s) => s.setResearchTopics);
  const addResearchTopic = useNewsletterStore((s) => s.addResearchTopic);
  const removeResearchTopic = useNewsletterStore((s) => s.removeResearchTopic);
  const setSelectedTone = useNewsletterStore((s) => s.setSelectedTone);
  const setCustomPrompt = useNewsletterStore((s) => s.setCustomPrompt);
  const setMaxArticles = useNewsletterStore((s) => s.setMaxArticles);
  const clearFormDraft = useNewsletterStore((s) => s.clearFormDraft);

  return {
    topics,
    tone,
    customPrompt,
    maxArticles,
    hasTopics,
    setResearchTopics,
    addResearchTopic,
    removeResearchTopic,
    setSelectedTone,
    setCustomPrompt,
    setMaxArticles,
    clearFormDraft,
  };
}

export default useNewsletterStore;
