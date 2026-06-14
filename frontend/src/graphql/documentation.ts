import { gql } from '@apollo/client';

export const GET_DOCUMENTATION_CATEGORIES = gql`
  query GetDocumentationCategories {
    documentationCategories {
      id
      title
      icon
      order
      isActive
      articles {
        id
        title
        content
        order
        isActive
        createdAt
        updatedAt
      }
    }
  }
`;

export const GET_DOCUMENTATION_ARTICLES = gql`
  query GetDocumentationArticles($categoryId: Int!) {
    documentationArticles(categoryId: $categoryId) {
      id
      categoryId
      title
      content
      order
      isActive
      createdAt
      updatedAt
    }
  }
`;

export const CREATE_DOCUMENTATION_CATEGORY = gql`
  mutation CreateDocumentationCategory($input: DocumentationCategoryInput!) {
    createDocumentationCategory(input: $input) {
      id
      title
      icon
      order
      isActive
    }
  }
`;

export const UPDATE_DOCUMENTATION_CATEGORY = gql`
  mutation UpdateDocumentationCategory($id: Int!, $input: DocumentationCategoryInput!) {
    updateDocumentationCategory(id: $id, input: $input) {
      id
      title
      icon
      order
      isActive
    }
  }
`;

export const DELETE_DOCUMENTATION_CATEGORY = gql`
  mutation DeleteDocumentationCategory($id: Int!) {
    deleteDocumentationCategory(id: $id)
  }
`;

export const CREATE_DOCUMENTATION_ARTICLE = gql`
  mutation CreateDocumentationArticle($input: DocumentationArticleInput!) {
    createDocumentationArticle(input: $input) {
      id
      categoryId
      title
      content
      order
      isActive
      createdAt
      updatedAt
    }
  }
`;

export const UPDATE_DOCUMENTATION_ARTICLE = gql`
  mutation UpdateDocumentationArticle($id: Int!, $input: DocumentationArticleInput!) {
    updateDocumentationArticle(id: $id, input: $input) {
      id
      categoryId
      title
      content
      order
      isActive
      createdAt
      updatedAt
    }
  }
`;

export const DELETE_DOCUMENTATION_ARTICLE = gql`
  mutation DeleteDocumentationArticle($id: Int!) {
    deleteDocumentationArticle(id: $id)
  }
`;

export const REORDER_DOCUMENTATION_ARTICLES = gql`
  mutation ReorderDocumentationArticles($categoryId: Int!, $articleIds: [Int!]!) {
    reorderDocumentationArticles(categoryId: $categoryId, articleIds: $articleIds)
  }
`;
