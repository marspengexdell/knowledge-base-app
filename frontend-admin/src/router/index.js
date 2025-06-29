import { createRouter, createWebHistory } from 'vue-router';

// --- View Components ---
// Import all the actual view components we have created.
import KnowledgeBase from '../views/KnowledgeBase.vue';
import ModelManagement from '../views/ModelManagement.vue';
import FeedbackReview from '../views/FeedbackReview.vue';
import DocumentManagement from '../views/DocumentManagement.vue';

// --- Route Definitions ---
const routes = [
  {
    path: '/',
    redirect: '/knowledge-base',
  },
  {
    path: '/knowledge-base',
    name: 'KnowledgeBase',
    component: KnowledgeBase,
    meta: { title: '知识库管理' }
  },
  {
    path: '/model-management',
    name: 'ModelManagement',
    component: ModelManagement,
    meta: { title: '模型管理' }
  },
  {
    path: '/feedback-review',
    name: 'FeedbackReview',
    // Use the actual component here
    component: FeedbackReview,
    meta: { title: '反馈审查' }
  },
  {
    path: '/document-management',
    name: 'DocumentManagement',
    component: DocumentManagement,
    meta: { title: '文档管理' }
  },
];

// --- Router Instance ---
const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
