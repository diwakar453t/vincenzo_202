import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import api from "../../services/api";

export const fetchResource = createAsyncThunk("resources/fetch", async (resource: string) => {
  const response = await api.get(`/${resource}/`);
  return { resource, items: response.data };
});

export const createResource = createAsyncThunk("resources/create", async ({ resource, payload }: { resource: string; payload: Record<string, unknown> }) => {
  const response = await api.post(`/${resource}/`, payload);
  return { resource, item: response.data };
});

export const updateResource = createAsyncThunk("resources/update", async ({ resource, id, payload }: { resource: string; id: number; payload: Record<string, unknown> }) => {
  const response = await api.put(`/${resource}/${id}`, payload);
  return { resource, item: response.data };
});

export const deleteResource = createAsyncThunk("resources/delete", async ({ resource, id }: { resource: string; id: number }) => {
  await api.delete(`/${resource}/${id}`);
  return { resource, id };
});

const resourcesSlice = createSlice({
  name: "resources",
  initialState: { byResource: {} as Record<string, unknown[]> },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchResource.fulfilled, (state, action) => {
        state.byResource[action.payload.resource] = action.payload.items;
      })
      .addCase(createResource.fulfilled, (state, action) => {
        const current = (state.byResource[action.payload.resource] ?? []) as unknown[];
        state.byResource[action.payload.resource] = [action.payload.item, ...current];
      })
      .addCase(updateResource.fulfilled, (state, action) => {
        const current = (state.byResource[action.payload.resource] ?? []) as Record<string, unknown>[];
        state.byResource[action.payload.resource] = current.map((item) => item.id === action.payload.item.id ? action.payload.item : item);
      })
      .addCase(deleteResource.fulfilled, (state, action) => {
        const current = (state.byResource[action.payload.resource] ?? []) as Record<string, unknown>[];
        state.byResource[action.payload.resource] = current.filter((item) => item.id !== action.payload.id);
      });
  },
});

export default resourcesSlice.reducer;
