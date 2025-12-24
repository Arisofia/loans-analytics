// Meta Graph API client wrapper
import axios from 'axios';

export class MetaGraphClient {
  private accessToken: string;
  private apiVersion: string;

  constructor(accessToken: string, apiVersion = 'v17.0') {
    this.accessToken = accessToken;
    this.apiVersion = apiVersion;
  }

  async get(path: string, params: Record<string, any> = {}) {
    const url = `https://graph.facebook.com/${this.apiVersion}/${path}`;
    const response = await axios.get(url, {
      params: { ...params, access_token: this.accessToken },
    });
    return response.data;
  }
}
