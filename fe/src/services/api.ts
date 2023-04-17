// @ts-ignore
/* eslint-disable */
import { request } from 'umi';
import { setLocale, getLocale, FormattedMessage } from 'umi';

/** 获取当前的用户 GET /api/currentUser */
export async function currentUser(options?: { [key: string]: any }) {
  return request<API.CurrentUser>('/api/currentUser', {
    method: 'GET',
    ...(options || {}),
  });
}

/** 此处后端没有提供注释 GET /api/notices */
export async function getNotices(options?: { [key: string]: any }) {
  return request<API.NoticeIconList>('/api/notices', {
    method: 'GET',
    ...(options || {}),
  });
}

export async function getNodeList(query: string){
  const lang = getLocale()
  return request('/api/getNodeList', {
    method: 'GET',
    params: {
      'query': query
    }
  })
}

export async function getIndividualAnalysis(paramData: any){
  const lang = getLocale()
  return request('/api/getIndividualAnalysis', {
    method: 'POST',
    data: {
      lang,
      ...paramData
    }
  })
}

export async function getGroupAnalysis(paramData: any){
  const lang = getLocale()
  return request('/api/getGroupAnalysis',{
    method: 'POST',
    data: {
      lang,
      ...paramData
    }
  })
}