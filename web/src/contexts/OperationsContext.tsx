/* eslint-disable react-refresh/only-export-components */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useAuth } from "@contexts/AuthContext";
import { api } from "@lib/api";
import type {
  OrganizationAccess,
  OrganizationsResponse,
} from "@/features/operations/apiTypes";

const STORAGE_KEY = "humq.selectedOrganizationId";

interface OperationsContextValue {
  loading: boolean;
  organizations: OrganizationAccess[];
  refreshOrganizations: () => Promise<void>;
  selectedOrganization: OrganizationAccess | null;
  selectOrganization: (organizationId: number) => void;
}

const OperationsContext = createContext<OperationsContextValue | undefined>(
  undefined,
);

export const OperationsProvider = ({ children }: { children: ReactNode }) => {
  const { account, loading: authLoading } = useAuth();
  const [organizations, setOrganizations] = useState<OrganizationAccess[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(() => {
    const saved = window.localStorage.getItem(STORAGE_KEY);
    return saved ? Number(saved) : null;
  });
  const [loading, setLoading] = useState(true);

  const refreshOrganizations = useCallback(async () => {
    if (!account) {
      setOrganizations([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const response = await api.get<OrganizationsResponse>("/organizations");
      setOrganizations(response.organizations);
      setSelectedId((current) => {
        if (
          current &&
          response.organizations.some(
            (organization) => organization.organization_id === current,
          )
        ) {
          return current;
        }
        return (
          response.organizations.find(
            (organization) => organization.kind === "INTERNAL",
          )?.organization_id ??
          response.organizations[0]?.organization_id ??
          null
        );
      });
    } catch {
      setOrganizations([]);
    } finally {
      setLoading(false);
    }
  }, [account]);

  useEffect(() => {
    if (!authLoading) void refreshOrganizations();
  }, [authLoading, refreshOrganizations]);

  useEffect(() => {
    if (selectedId) window.localStorage.setItem(STORAGE_KEY, String(selectedId));
    else window.localStorage.removeItem(STORAGE_KEY);
  }, [selectedId]);

  const selectOrganization = useCallback((organizationId: number) => {
    setSelectedId(organizationId);
  }, []);

  const selectedOrganization =
    organizations.find(
      (organization) => organization.organization_id === selectedId,
    ) ?? null;

  const value = useMemo<OperationsContextValue>(
    () => ({
      loading,
      organizations,
      refreshOrganizations,
      selectedOrganization,
      selectOrganization,
    }),
    [
      loading,
      organizations,
      refreshOrganizations,
      selectedOrganization,
      selectOrganization,
    ],
  );

  return (
    <OperationsContext.Provider value={value}>
      {children}
    </OperationsContext.Provider>
  );
};

export const useOperations = () => {
  const context = useContext(OperationsContext);
  if (!context) {
    throw new Error("useOperations must be used within an OperationsProvider");
  }
  return context;
};
