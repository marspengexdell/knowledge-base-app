import { createRouter, createWebHistory } from 'vue-router';

import KnowledgeBase from '../views/KnowledgeBase.vue';
import ModelManagement from '../views/ModelManagement.vue';
import FeedbackReview from '../views/FeedbackReview.vue';
import DocumentManagement from '../views/DocumentManagement.vue';
import Dashboard from '../views/Dashboard.vue';

const routes = [
  { path: '/admin/', name: 'Home', component: Dashboard },
  { path: '/admin/model-management', name: 'ModelManagement', component: ModelManagement },
  { path: '/admin/knowledge-base', name: 'KnowledgeBase', component: KnowledgeBase },
  { path: '/admin/feedback-review', name: 'FeedbackReview', component: FeedbackReview },
  { path: '/admin/document-management', name: 'DocumentManagement', component: DocumentManagement },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
