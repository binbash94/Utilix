import React, { createContext, useContext, useEffect, useState } from "react";
import { getStoredConfig, saveConfig } from "./config";

export type ConfigContextType = {
  apiBase: string;
  token: string;
  setApiBase: (apiBase: string) => void;
  setToken: (token: string) => void;
};

const ConfigContext = createContext<ConfigContextType>({
  apiBase: "",
  token: "",
  setApiBase: () => {},
  setToken: () => {},
});

export const ConfigProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [apiBase, setApiBase] = useState("");
  const [token, setToken] = useState("");

  useEffect(() => {
    const cfg = getStoredConfig();
    setApiBase(cfg.apiBase || "");
    setToken(cfg.token || "");
  }, []);

  useEffect(() => {
    saveConfig({ apiBase, token });
  }, [apiBase, token]);

  return (
    <ConfigContext.Provider value={{ apiBase, token, setApiBase, setToken }}>
      {children}
    </ConfigContext.Provider>
  );
};

export const useConfig = () => useContext(ConfigContext);