/*
 * Router Configuration
 * Vue Router for AI English Learning System
 */
import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Chat from '../views/Chat.vue'
import Listening from '../views/Listening.vue'
import Pronunciation from '../views/Pronunciation.vue'
import Vocabulary from '../views/Vocabulary.vue'
import Writing from '../views/Writing.vue'
import Stats from '../views/Stats.vue'
import Dictation from '../views/Dictation.vue'
import Grammar from '../views/Grammar.vue'
import Settings from '../views/Settings.vue'

const routes = [
  {
    path: '/',
    redirect: '/home'
  },
  {
    path: '/home',
    name: 'Home',
    component: Home,
    meta: { title: '首页', icon: 'House' }
  },
  {
    path: '/chat',
    name: 'Chat',
    component: Chat,
    meta: { title: 'AI口语陪练', icon: 'ChatDotRound' }
  },
  {
    path: '/listening',
    name: 'Listening',
    component: Listening,
    meta: { title: '听力训练', icon: 'Headset' }
  },
  {
    path: '/pronunciation',
    name: 'Pronunciation',
    component: Pronunciation,
    meta: { title: '发音评测', icon: 'Microphone' }
  },
  {
    path: '/vocabulary',
    name: 'Vocabulary',
    component: Vocabulary,
    meta: { title: '单词本', icon: 'Notebook' }
  },
  {
    path: '/writing',
    name: 'Writing',
    component: Writing,
    meta: { title: '写作批改', icon: 'Edit' }
  },
  {
    path: '/stats',
    name: 'Stats',
    component: Stats,
    meta: { title: '学习中心', icon: 'DataAnalysis' }
  },
  {
    path: '/dictation',
    name: 'Dictation',
    component: Dictation,
    meta: { title: '单词默写', icon: 'EditPen' }
  },
  {
    path: '/grammar',
    name: 'Grammar',
    component: Grammar,
    meta: { title: '语法学习', icon: 'Reading' }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings,
    meta: { title: '设置', icon: 'Setting' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router