import { useTranslation } from 'react-i18next';
import { Languages } from "lucide-react";
import { Button } from '@/components/ui/button';

export function LanguageSwitcher() {
  const { i18n } = useTranslation();

  const toggleLanguage = () => {
    const newLang = i18n.language === 'ko' ? 'en' : 'ko';
    i18n.changeLanguage(newLang);
  };

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={toggleLanguage}
      title={i18n.language === 'ko' ? 'Switch to English' : '한국어로 전환'}
    >
      <Languages className="h-4 w-4 mr-1" />
      {i18n.language === 'ko' ? 'EN' : 'KO'}
    </Button>
  );
}
