import React from 'react';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Image from '@tiptap/extension-image';
import Link from '@tiptap/extension-link';
import Placeholder from '@tiptap/extension-placeholder';
import { Box, Paper, IconButton, Tooltip, Divider, TextField } from '@mui/material';
import {
  FormatBold,
  FormatItalic,
  FormatListBulleted,
  FormatListNumbered,
  FormatQuote,
  Code,
  Title,
  Image as ImageIcon,
  Link as LinkIcon,
  Undo,
  Redo,
} from '@mui/icons-material';

interface RichTextEditorProps {
  content: string;
  onChange: (html: string) => void;
  placeholder?: string;
}

const RichTextEditor: React.FC<RichTextEditorProps> = ({ content, onChange, placeholder = 'Напишете съдържание...' }) => {
  const [linkUrl, setLinkUrl] = React.useState('');
  const [showLinkInput, setShowLinkInput] = React.useState(false);

  const editor = useEditor({
    extensions: [
      StarterKit,
      Image.configure({
        HTMLAttributes: {
          class: 'tiptap-image',
        },
      }),
      Link.configure({
        openOnClick: false,
        HTMLAttributes: {
          class: 'tiptap-link',
        },
      }),
      Placeholder.configure({
        placeholder,
      }),
    ],
    content,
    onUpdate: ({ editor }) => {
      onChange(editor.getHTML());
    },
  });

  if (!editor) {
    return null;
  }

  const addImage = () => {
    const url = window.prompt('URL на изображението:');
    if (url) {
      editor.chain().focus().setImage({ src: url }).run();
    }
  };

  const addLink = () => {
    if (linkUrl) {
      editor.chain().focus().extendMarkRange('link').setLink({ href: linkUrl }).run();
      setLinkUrl('');
      setShowLinkInput(false);
    }
  };

  return (
    <Paper elevation={1} sx={{ border: 1, borderColor: 'divider' }}>
      <Box sx={{ p: 1, display: 'flex', flexWrap: 'wrap', gap: 0.5, borderBottom: 1, borderColor: 'divider' }}>
        <Tooltip title="Undo">
          <IconButton size="small" onClick={() => editor.chain().focus().undo().run()} disabled={!editor.can().undo()}>
            <Undo fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip title="Redo">
          <IconButton size="small" onClick={() => editor.chain().focus().redo().run()} disabled={!editor.can().redo()}>
            <Redo fontSize="small" />
          </IconButton>
        </Tooltip>
        <Divider orientation="vertical" flexItem sx={{ mx: 1 }} />
        <Tooltip title="Заглавие">
          <IconButton
            size="small"
            onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
            color={editor.isActive('heading', { level: 2 }) ? 'primary' : 'default'}
          >
            <Title fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip title="Bold">
          <IconButton
            size="small"
            onClick={() => editor.chain().focus().toggleBold().run()}
            color={editor.isActive('bold') ? 'primary' : 'default'}
          >
            <FormatBold fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip title="Italic">
          <IconButton
            size="small"
            onClick={() => editor.chain().focus().toggleItalic().run()}
            color={editor.isActive('italic') ? 'primary' : 'default'}
          >
            <FormatItalic fontSize="small" />
          </IconButton>
        </Tooltip>
        <Divider orientation="vertical" flexItem sx={{ mx: 1 }} />
        <Tooltip title="Списък">
          <IconButton
            size="small"
            onClick={() => editor.chain().focus().toggleBulletList().run()}
            color={editor.isActive('bulletList') ? 'primary' : 'default'}
          >
            <FormatListBulleted fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip title="Номериран списък">
          <IconButton
            size="small"
            onClick={() => editor.chain().focus().toggleOrderedList().run()}
            color={editor.isActive('orderedList') ? 'primary' : 'default'}
          >
            <FormatListNumbered fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip title="Цитат">
          <IconButton
            size="small"
            onClick={() => editor.chain().focus().toggleBlockquote().run()}
            color={editor.isActive('blockquote') ? 'primary' : 'default'}
          >
            <FormatQuote fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip title="Код">
          <IconButton
            size="small"
            onClick={() => editor.chain().focus().toggleCodeBlock().run()}
            color={editor.isActive('codeBlock') ? 'primary' : 'default'}
          >
            <Code fontSize="small" />
          </IconButton>
        </Tooltip>
        <Divider orientation="vertical" flexItem sx={{ mx: 1 }} />
        <Tooltip title="Изображение">
          <IconButton size="small" onClick={addImage}>
            <ImageIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip title="Линк">
          <IconButton
            size="small"
            onClick={() => setShowLinkInput(!showLinkInput)}
            color={editor.isActive('link') ? 'primary' : 'default'}
          >
            <LinkIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Box>

      {showLinkInput && (
        <Box sx={{ p: 1, display: 'flex', gap: 1, borderBottom: 1, borderColor: 'divider', bgcolor: 'grey.50' }}>
          <TextField
            size="small"
            placeholder="https://example.com"
            value={linkUrl}
            onChange={(e) => setLinkUrl(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && addLink()}
            sx={{ flex: 1 }}
          />
          <IconButton onClick={addLink} color="primary">
            <LinkIcon />
          </IconButton>
        </Box>
      )}

      <Box sx={{ p: 2 }}>
        <EditorContent
          editor={editor}
          style={{
            minHeight: '300px',
            outline: 'none',
          }}
        />
      </Box>

      <style>{`
        .tiptap {
          outline: none;
          min-height: 300px;
        }
        .tiptap p.is-editor-empty:first-child::before {
          color: #adb5bd;
          content: attr(data-placeholder);
          float: left;
          height: 0;
          pointer-events: none;
        }
        .tiptap h1, .tiptap h2, .tiptap h3 {
          margin-top: 1rem;
          margin-bottom: 0.5rem;
        }
        .tiptap ul, .tiptap ol {
          padding-left: 1.5rem;
        }
        .tiptap blockquote {
          border-left: 3px solid #ddd;
          margin-left: 0;
          margin-right: 0;
          padding-left: 1rem;
        }
        .tiptap code {
          background-color: #f5f5f5;
          border-radius: 0.25rem;
          padding: 0.125rem 0.25rem;
          font-family: monospace;
        }
        .tiptap pre {
          background-color: #f5f5f5;
          border-radius: 0.5rem;
          padding: 1rem;
          overflow-x: auto;
        }
        .tiptap pre code {
          background: none;
          padding: 0;
        }
        .tiptap-image {
          max-width: 100%;
          height: auto;
          margin: 1rem 0;
        }
        .tiptap-link {
          color: #1976d2;
          text-decoration: underline;
          cursor: pointer;
        }
      `}</style>
    </Paper>
  );
};

export default RichTextEditor;
