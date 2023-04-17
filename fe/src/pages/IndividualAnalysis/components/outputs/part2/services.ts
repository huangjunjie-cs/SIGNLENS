import { request } from 'umi';

export async function getXYRelationship(x: string, y:string) {
  return request('/api/getRelationship', {
    params:{
      x,
      y
    }
  });
}
