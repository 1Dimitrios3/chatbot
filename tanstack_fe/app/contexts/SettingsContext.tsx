import { createContext, PropsWithChildren, useContext, useState } from 'react';
import { FileType } from '~/types';

interface SettingsContextType {
  selectModel: string;
  setSelectModel: (model: string) => void;
  selectFileType: FileType;
  setSelectFileType: (fileType: FileType) => void;
  chunkSize: string;
  setChunkSize: (chunk: string) => void;
}

const SettingsContext = createContext({} as SettingsContextType);

export const SettingsProvider = ({ children }: PropsWithChildren) => {
  const [selectModel, setSelectModel] = useState("gpt-4o-mini");
  const [selectFileType, setSelectFileType] = useState<FileType>("pdf");
  const [chunkSize, setChunkSize] = useState('');

  return (
    <SettingsContext.Provider value={{ selectModel, setSelectModel, selectFileType, setSelectFileType, chunkSize, setChunkSize }}>
      {children}
    </SettingsContext.Provider>
  );
};

export const useSettings = () => {
  return useContext(SettingsContext);
};
