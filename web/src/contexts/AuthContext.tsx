/* eslint-disable react-refresh/only-export-components */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import type { ReactNode } from "react";
import type { Account } from "types/models";
import { api } from "@lib/api";
import type { GetCurrentAccountResponse } from "@/features/accounts/apiTypes";

interface AuthContextType {
  account: Account | null;
  accessToken: string | null;
  setAccount: (account: Account | null) => void;
  setAccessToken: (token: string | null) => void;
  logout: () => Promise<void>;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [account, setAccount] = useState<Account | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const logout = useCallback(async () => {
    setAccount(null);
    setAccessToken(null);
    try {
      await api.post("/auth/logout");
    } catch {
      // keep local logout state even if the server request fails
    }
  }, []);

  useEffect(() => {
    api.setAccessToken(accessToken);
  }, [accessToken]);

  useEffect(() => {
    api.setAccessTokenCallback(setAccessToken);

    return () => api.setAccessTokenCallback(undefined);
  }, []);

  useEffect(() => {
    const fetchAccount = async () => {
      try {
        const res = await api.get<GetCurrentAccountResponse>("/accounts/me");
        setAccount(res.account);
      } catch {
        setAccount(null);
      } finally {
        setLoading(false);
      }
    };
    fetchAccount();
  }, []);

  const value = useMemo<AuthContextType>(
    () => ({
      account,
      accessToken,
      setAccount,
      setAccessToken,
      logout,
      loading,
    }),
    [accessToken, account, loading, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within an AuthProvider");
  return context;
};
