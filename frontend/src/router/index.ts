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
    meta: { title: '首页', icon: 'House', color: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', desc: '查看学习概览' }
  },
  {
    path: '/chat',
    name: 'Chat',
    component: Chat,
    meta: { title: 'AI口语陪练', icon: 'ChatDotRound', color: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', desc: '与AI对话练习' }
  },
  {
    path: '/listening',
    name: 'Listening',
    component: Listening,
    meta: { title: '听力训练', icon: 'Headset', color: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', desc: '提升听力理解' }
  },
  {
    path: '/pronunciation',
    name: 'Pronunciation',
    component: Pronunciation,
    meta: { title: '发音评测', icon: 'Microphone', color: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)', desc: 'AI评分你的发音' }
  },
  {
    path: '/vocabulary',
    name: 'Vocabulary',
    component: Vocabulary,
    meta: { title: '单词本', icon: 'Notebook', color: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)', desc: '艾宾浩斯记忆' }
  },
  {
    path: '/writing',
    name: 'Writing',
    component: Writing,
    meta: { title: '写作批改', icon: 'Edit', color: 'linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)', desc: 'AI语法纠错' }
  },
  {
    path: '/stats',
    name: 'Stats',
    component: Stats,
    meta: { title: '学习中心', icon: 'DataAnalysis', color: 'linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)', desc: '查看学习数据' }
  },
  {
    path: '/dictation',
    name: 'Dictation',
    component: Dictation,
    meta: { title: '单词默写', icon: 'EditPen', color: 'linear-gradient(135deg, #f6d365 0%, #fda085 100%)', desc: '检验背单词' }
  },
  {
    path: '/grammar',
    name: 'Grammar',
    component: Grammar,
    meta: { title: '语法学习', icon: 'Reading', color: 'linear-gradient(135deg, #96fbc4 0%, #f9f586 100%)', desc: '系统学习语法' }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings,
    meta: { title: '设置', icon: 'Setting', color: 'linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%)', desc: '个性化配置' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router