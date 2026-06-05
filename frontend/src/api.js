import axios from "axios";

const api = axios.create({ baseURL: "/api" });

export function generateScript(title, chapters) {
  return api.post("/script/generate", { title, chapters, style: "screenplay" });
}

export function validateYaml(yamlText) {
  return api.post("/script/validate", { yaml_text: yamlText });
}
